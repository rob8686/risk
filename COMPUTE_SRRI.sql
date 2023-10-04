USE [METIS2]
GO
/****** Object:  StoredProcedure [dbo].[COMPUTE_SRRI]    Script Date: 07-07-2023 3.49.11 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO


CREATE PROCEDURE [dbo].[COMPUTE_SRRI]
@report_date date
AS
BEGIN

--SET NOCOUNT ON;
SET ANSI_WARNINGS OFF;

begin try

	
	insert into [UTILITY].[APP_LOGS] ([EntryID], [Type] , [EntryDate] ,[ApplicationName] )
	values (newid(), 'ProcedureStart', getdate(), 'COMPUTE_SRRI' )

	--IMPORTANT ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	--ECR 20190722: ONLY USE PROXY FOR MONHTLY SRRI !!!
	------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------	

	-- clean SRRI warnings

	delete from utility.warnings
	where warning_message like '%SRRI%'

	--VPS 20190723: SRRI shadow monitoring. Check if all subfunds in a given fund were setup
	-- Table to keep track of subfunds for which we do not want to see warning messages
	DECLARE @disable_warn TABLE(
		Subfund_ID int
	)
	INSERT INTO  @disable_warn VALUES (54)
	INSERT INTO  @disable_warn VALUES (8023)
	INSERT INTO  @disable_warn VALUES (8024)
	INSERT INTO  @disable_warn VALUES (8025)
	INSERT INTO  @disable_warn VALUES (8026)
	INSERT INTO  @disable_warn VALUES (8027)
	INSERT INTO  @disable_warn VALUES (8029)
	INSERT INTO  @disable_warn VALUES (8032)
	INSERT INTO  @disable_warn VALUES (8034)
	INSERT INTO  @disable_warn VALUES (8035)
	INSERT INTO  @disable_warn VALUES (8036)
	INSERT INTO  @disable_warn VALUES (8037)
	INSERT INTO  @disable_warn VALUES (8039)
	INSERT INTO  @disable_warn VALUES (8040)
	INSERT INTO  @disable_warn VALUES (8041)
	INSERT INTO  @disable_warn VALUES (8042)
	INSERT INTO  @disable_warn VALUES (8043)
	INSERT INTO  @disable_warn VALUES (8044)
	INSERT INTO  @disable_warn VALUES (8045)
	INSERT INTO  @disable_warn VALUES (8455)
	INSERT INTO  @disable_warn VALUES (8456)
	INSERT INTO  @disable_warn VALUES (8488)
	INSERT INTO  @disable_warn VALUES (8651)
	INSERT INTO  @disable_warn VALUES (5909)
	INSERT INTO  @disable_warn VALUES (8663) -- CAPEX ALPHA FUND is done manually by reporting. Benchmark not available
	INSERT INTO  @disable_warn VALUES (9529) -- TECHNICAL SUBFUND FOR DUMMY SHC 

	DECLARE @temp_exclude TABLE(
		Subfund_ID int,
		ShareClass_ID int
	)

	INSERT INTO		utility.warnings (Table_Name, Field_Name, Field_Value, Field_2_Name, Field_2_Value, Warning_Message)
	--OUTPUT  INSERTED.Field_Value, NULL INTO @temp_exclude
	SELECT DISTINCT 'MASTER.SUBFUNDS'
		, 'Subfund_ID'
		, msf.Subfund_ID
		, 'Fund_ID'
		, f_enabled.Fund_ID
		, 'MISSING SRRI monitoring - ' + f_enabled.Fund_Name + ' - '+ msf.Subfund_Name
	FROM.MASTER.Subfunds  msf
	INNER JOIN
		(Select f.Fund_ID, f.Fund_Name, SUM(CAST(sf.Subfund_SRRI AS INT)) as enabled_sf
		FROM MASTER.FUNDS f
		INNER JOIN MASTER.SUBFUNDS sf ON sf.Fund_ID = f.Fund_ID
		WHERE 1=1
			AND f.Fund_Is_Enabled = 1
			AND ISNULL(f.Fund_End_Date, '2100-01-01') >= @report_date 
			AND ISNULL(sf.Subfund_End_Date, '2100-01-01') >= @report_date
			AND sf.Is_Closed = 0
			AND f.Fund_Legal_Regime_ID = 1
		GROUP BY f.Fund_ID, f.Fund_Name
		HAVING 1=1
			AND SUM(CAST(sf.Subfund_SRRI AS INT )) > 0
			--AND COUNT(sf.Subfund_ID) > 1
		) AS f_enabled ON f_enabled.Fund_ID = msf.Fund_ID
	INNER JOIN MASTER.SHARE_CLASSES sc ON sc.Subfund_ID = msf.Subfund_ID
	WHERE 1=1
		AND msf.Subfund_SRRI = 0
		AND ISNULL(msf.Subfund_End_Date, '2100-01-01') >= @report_date
		AND msf.Is_Closed = 0
		AND msf.Subfund_Is_Enabled = 1
		AND NOT EXISTS (SELECT * FROM @disable_warn dw WHERE dw.Subfund_ID = msf.Subfund_ID)
	ORDER BY f_enabled.Fund_ID

	-- check for missing investment policies

	insert into		utility.warnings (Table_Name, Field_Name, Field_Value, Warning_Message)
	OUTPUT  INSERTED.Field_Value, NULL   INTO @temp_exclude
	SELECT distinct	'HISTORY.INVESTMENT_POLICY', 'Subfund_ID', s.Subfund_ID, 'Missing SRRI Classification'
	from
		master.subfunds s left join
		history.investment_policy p inner join
		(SELECT Subfund_ID, MAX(Effective_Date) AS dt
		FROM     HISTORY.INVESTMENT_POLICY
		GROUP BY Subfund_ID) h 
		on h.Subfund_ID = p.Subfund_ID and h.dt = p.Effective_Date
		on s.Subfund_ID = p.Subfund_ID
	WHERE 
		s.Subfund_SRRI = 1 and s.Fund_ID !=33  and p.Subfund_ID is null

	-- PB 20210225: update Monthly_Risk_Free_Rate for absolute return funds

	IF OBJECT_ID('tempdb..#temp_market_value') IS NOT NULL DROP TABLE #temp_market_value

	SELECT mkd.Instrument_ID, z.Instrument_Currency_ID, mkd.Value
	INTO #temp_market_value
	FROM HISTORY.MARKET_DATA AS mkd INNER JOIN 
		(SELECT md.Instrument_ID,inst.Instrument_Currency_ID, MAX(md.Date) AS vDate
		 FROM HISTORY.MARKET_DATA AS md INNER JOIN
			(SELECT Instrument_Currency_ID, 
				MIN(Instrument_ID) AS Instrument_ID
			 FROM MASTER.INSTRUMENTS 
			 WHERE Instrument_CA_Internal_Code='3M'
				AND Instrument_Is_Enabled=1
			 GROUP BY Instrument_Currency_ID) AS inst ON inst.Instrument_ID=md.Instrument_ID
		 WHERE md.Field_ID=4
		 GROUP BY md.Instrument_ID,inst.Instrument_Currency_ID) AS z ON z.Instrument_ID = mkd.Instrument_ID AND z.vDate=mkd.Date
	WHERE mkd.Field_ID=4

	UPDATE arf
	SET arf.Monthly_Risk_Free_Rate = t.Value
	FROM HISTORY.ABSOLUTE_RETURN_FUNDS AS arf 
		INNER JOIN MASTER.SHARE_CLASSES AS sc ON sc.Share_Class_ID = arf.Share_Class_ID
		INNER JOIN #temp_market_value AS t ON t.Instrument_Currency_ID=sc.Share_Class_Currency_ID

	-- update Annual_Volatility_Limit for absolute return funds

	update	HISTORY.ABSOLUTE_RETURN_FUNDS
	set		Annual_Volatility_Limit = sqrt(12) * (sqrt(2 * (Monthly_VaR_Limit + Monthly_Risk_Free_Rate) + VaR_Confidence_Multiplier * VaR_Confidence_Multiplier) - VaR_Confidence_Multiplier)
	where	Monthly_VaR_Limit is not null and Monthly_Risk_Free_Rate is not null and VaR_Confidence_Multiplier is not null


	-- check for missing data for absolute return funds

	insert into		utility.warnings (Table_Name, Field_Name, Field_Value, Warning_Message)
	OUTPUT   NULL, INSERTED.Field_Value INTO @temp_exclude
	SELECT distinct	'HISTORY.ABSOLUTE_RETURN_FUNDS', 'Share_Class_ID', t.share_class_id, 'Missing SRRI Volatility Limit'
	FROM     
			HISTORY.ABSOLUTE_RETURN_FUNDS a 
		right JOIN
            (select MASTER.SHARE_CLASSES.share_class_id, HISTORY.INVESTMENT_POLICY.effective_date
			from master.subfunds inner join MASTER.SHARE_CLASSES on master.subfunds.Subfund_ID = MASTER.SHARE_CLASSES.Subfund_ID
			inner join HISTORY.INVESTMENT_POLICY ON MASTER.SHARE_CLASSES.Subfund_ID = HISTORY.INVESTMENT_POLICY.Subfund_ID
			WHERE   master.subfunds.Subfund_SRRI = 1
					and HISTORY.INVESTMENT_POLICY.Subfund_SRRI_Classification_ID = 2
					and MASTER.SHARE_CLASSES.Share_Class_Is_Enabled = 1) t
		on a.Share_Class_ID = t.Share_Class_ID
	where
		a.Annual_Volatility_Limit is null

	
	-- check for missing published SRRIs

	insert into	utility.warnings (Table_Name, Field_Name, Field_Value, Warning_Message)
	--OUTPUT   NULL, INSERTED.Field_Value INTO @temp_exclude
	SELECT  'HISTORY.SRRI', 'Share_Class_ID', MASTER.SHARE_CLASSES.Share_Class_ID, 'Missing Published SRRI'
	FROM     MASTER.SUBFUNDS INNER JOIN
					  MASTER.SHARE_CLASSES ON MASTER.SUBFUNDS.Subfund_ID = MASTER.SHARE_CLASSES.Subfund_ID LEFT OUTER JOIN
					  HISTORY.SRRI ON MASTER.SHARE_CLASSES.Share_Class_ID = HISTORY.SRRI.Share_Class_ID
	WHERE  (MASTER.SUBFUNDS.Subfund_SRRI = 1) AND (MASTER.SHARE_CLASSES.Share_Class_Is_Enabled = 1) AND (HISTORY.SRRI.Share_Class_ID IS NULL) AND (MASTER.SHARE_CLASSES.Share_Class_End_Date IS NULL)

	-- check if shareclass activated has no reference currency
	insert into	utility.warnings (Table_Name, Field_Name, Field_Value, Warning_Message)
	OUTPUT   NULL, INSERTED.Field_Value INTO @temp_exclude
	SELECT 'HISTORY.SRRI', 'Share_Class_ID', MASTER.SHARE_CLASSES.Share_Class_ID, 'Missing Shareclass Currency SRRI'
	FROM MASTER.SUBFUNDS 
		INNER JOIN MASTER.SHARE_CLASSES ON MASTER.SUBFUNDS.Subfund_ID = MASTER.SHARE_CLASSES.Subfund_ID 
	WHERE  (MASTER.SUBFUNDS.Subfund_SRRI = 1) AND (MASTER.SHARE_CLASSES.Share_Class_Is_Enabled = 1) AND (MASTER.SHARE_CLASSES.Share_Class_Currency_ID = 33)
		AND NOT EXISTS (SELECT * FROM @disable_warn dw WHERE dw.Subfund_ID = MASTER.SUBFUNDS.Subfund_ID)


	-- VPS 20190723: Do not stop the proc but exclude sc\sf then they are not setup up correctly
		--if exists (select top 1 * from utility.warnings where warning_message like '%SRRI%')

		--begin

		--	insert into [UTILITY].[APP_LOGS] ([EntryID], [Type] , [EntryDate] ,[ApplicationName] )
		--	values (newid(), 'ProcedureInterruption', getdate(), 'COMPUTE_SRRI' )

		--	return
		--end


	DECLARE @end_date Date
	DECLARE @start_date Date
	DECLARE @start_date_4m Date

	SET @end_date = (SELECT MAX(Calendar_Date) FROM UTILITY.CALENDAR
					 WHERE Weekday = 5 AND Calendar_Date <= @report_date)
	
	--SET @start_date = DATEADD(mm, -64, @end_date)
	SET @start_date = DATEADD(mm, -67, @end_date)
	--ECR 2018-06-26 FundReporting wants 6M history / SSRS Reporting is not impacted, filtering for the last 4M
	--SET @start_date_4m = DATEADD(mm, -4, @end_date)
	--SET @start_date_4m = DATEADD(ww, -16, @end_date)
	SET @start_date_4m = DATEADD(ww, -28, @end_date) 
	--ECR 2018-06-26 FundReporting wants 6M history / SSRS Reporting is not impacted, filtering for the last 4M
	-- update share class start date

	UPDATE	 MASTER.SHARE_CLASSES
	SET      Share_Class_Start_Date = m.min_dt
	FROM     MASTER.SHARE_CLASSES INNER JOIN
				(SELECT Share_Class_ID, MIN(NAV_Date) AS min_dt
				FROM     HISTORY.NAVS
				GROUP BY Share_Class_ID) m
	ON		 MASTER.SHARE_CLASSES.Share_Class_ID = m.Share_Class_ID
	WHERE    MASTER.SHARE_CLASSES.Share_Class_Is_Enabled = 1




	truncate table [RESULTS].[SRRI_RETURNS]
	
	-- 20190801 ecr: WEEKLY SUBFUNDS
	IF OBJECT_ID('tempdb..#weekly_cal') IS NOT NULL DROP TABLE #weekly_cal
	IF OBJECT_ID('tempdb..#weekly_SF') IS NOT NULL DROP TABLE #weekly_SF
	
	SELECT nav.Share_Class_ID, nav.NAV_Date, cal.Cumulative_Week
		,MIN(nav.NAV_Date) OVER (PARTITION BY shc.Share_Class_ID, cal.Cumulative_Week ORDER BY cal.Cumulative_Week) AS dt
	INTO #weekly_cal
	FROM HISTORY.NAVS AS nav
	INNER JOIN MASTER.SHARE_CLASSES AS shc ON shc.Share_Class_ID = nav.Share_Class_ID
	INNER JOIN MASTER.SUBFUNDS AS sf ON sf.Subfund_ID = shc.Subfund_ID
	INNER JOIN UTILITY.CALENDAR AS cal ON cal.Calendar_Date = nav.NAV_Date
	WHERE 1=1
		AND sf.Subfund_NAV_Frequency_ID = 3
		-- VPS 20190819: Do not stop the proc but exclude sc\sf then they are not setup up correctly
		AND NOT EXISTS (SELECT * FROM @temp_exclude te  WHERE te.ShareClass_ID = shc.Share_Class_ID)
		AND  NOT EXISTS (SELECT * FROM @temp_exclude te  WHERE te.Subfund_ID = sf.Subfund_ID)
		--AND sf.Subfund_ID = 65
	ORDER BY shc.Share_Class_ID
	
	;WITH CTE AS 
	(SELECT DISTINCT Share_Class_ID, dt 
		,Cumulative_Week
	FROM #weekly_cal
	)

	SELECT  Share_Class_ID, dt AS [Start_Date], 0 AS Frequency_ID 
		,LEAD(dt) OVER (PARTITION BY Share_Class_ID ORDER BY dt ASC) AS [End_Date]
	INTO #weekly_SF
	FROM CTE 
	;--WEEKLY SUBFUNDS END


	-- insert start and end date for each share class, including only official nav dates;
	-- frequency_ID temporarily set to zero because it cannot be null
	insert into [RESULTS].[SRRI_RETURNS] (Share_Class_ID, [end_date], [start_date], Frequency_ID)
	SELECT C.Share_Class_ID, C.NAV_Date as [end_date], max(P.NAV_Date) as [start_date], 0
	FROM master.subfunds f inner join
		master.share_classes s on f.Subfund_ID = s.Subfund_ID inner join
		HISTORY.NAVS C on c.Share_Class_ID = s.Share_Class_ID
		INNER JOIN HISTORY.NAVS P ON (C.NAV_Date > P.NAV_Date) AND (C.Share_Class_ID = P.Share_Class_ID)
	where C.NAV_Date between @start_date and @end_date
		and c.is_nav_official = 1 and p.is_nav_official = 1 
		--20190801 ecr: excluding weekend days.....
		and datepart(weekday,C.NAV_Date) not in (1,7)
		AND datepart(weekday,P.NAV_Date) not in (1,7)
		and s.Share_Class_Is_Enabled = 1 and f.Subfund_SRRI = 1
		and (s.Share_Class_End_Date is null or s.Share_Class_End_Date <= @end_date)
		AND f.Subfund_NAV_Frequency_ID <>3
		-- VPS 20190723: Do not stop the proc but exclude sc\sf then they are not setup up correctly
		AND NOT EXISTS (SELECT * FROM @temp_exclude te  WHERE te.ShareClass_ID = s.Share_Class_ID)
		AND  NOT EXISTS (SELECT * FROM @temp_exclude te  WHERE te.Subfund_ID = f.Subfund_ID)
		--AND  f.Subfund_ID = 8693
	group by C.Share_Class_ID, C.NAV_Date
	UNION 
	SELECT  Share_Class_ID, [End_Date], [Start_Date], Frequency_ID 
	FROM #weekly_SF
	WHERE End_Date IS NOT NULL


	-- insert start and end date for each share class, including only official nav dates;
	-- frequency_ID temporarily set to zero because it cannot be null
	--insert into [RESULTS].[SRRI_RETURNS] (Share_Class_ID, [end_date], [start_date], Frequency_ID)
	--SELECT C.Share_Class_ID, C.NAV_Date as [end_date], max(P.NAV_Date) as [start_date], 0
	--FROM master.subfunds f inner join
	--	master.share_classes s on f.Subfund_ID = s.Subfund_ID inner join
	--	HISTORY.NAVS C on c.Share_Class_ID = s.Share_Class_ID
	--	INNER JOIN HISTORY.NAVS P 
	--	ON (C.NAV_Date > P.NAV_Date) AND (C.Share_Class_ID = P.Share_Class_ID)
	--where C.NAV_Date between @start_date and @end_date
	--	and c.is_nav_official = 1 and p.is_nav_official = 1 
	--	--20190801 ecr
	--	and datepart(weekday,C.NAV_Date) not in (1,7)
	--	AND datepart(weekday,P.NAV_Date) not in (1,7)
	--	--20190801 ecr-----
	--	and s.Share_Class_Is_Enabled = 1 and f.Subfund_SRRI = 1
	--	and (s.Share_Class_End_Date is null or s.Share_Class_End_Date <= @end_date)
	--group by C.Share_Class_ID, C.NAV_Date


	-- frequency_id set to the subfund OFFICIAL nav frequency
	update H
	--20190722 ECR: monthly SRRI
	--set H.Frequency_ID = s.Subfund_NAV_Official_Frequency_ID
	set H.Frequency_ID = IIF(S.SRRI_Frequency IS NULL, s.Subfund_NAV_Official_Frequency_ID, S.SRRI_Frequency) 	--20190722 ECR: new field SRRI_Frequency)
	from [RESULTS].[SRRI_RETURNS] H 
		inner join [master].SHARE_CLASSES M 
		on H.Share_Class_ID = M.Share_Class_ID
		inner join [master].subfunds S 
		on s.subfund_id = m.Subfund_ID
	
	--20190722 ECR: monthly SRRI
	;WITH CTE AS (SELECT res.*, ROW_NUMBER() OVER (PARTITION BY res.Share_Class_ID, cal.[Year], cal.[Month] ORDER BY cal.Calendar_Date ASC) AS nb
		, COUNT(res.Share_Class_ID) OVER (PARTITION BY res.Share_Class_ID, cal.[Year], cal.[Month] ) AS ct
		, datediff(day,Start_date,End_Date) AS nb_days
	FROM RESULTS.SRRI_RETURNS AS res
	INNER JOIN UTILITY.CALENDAR AS cal ON cal.Calendar_Date = res.End_Date
	WHERE 1=1	
		AND res.Frequency_ID = 5)

	DELETE FROM res
	FROM CTE  AS cte
	INNER JOIN RESULTS.SRRI_RETURNS AS res ON res.Share_Class_ID = cte.Share_Class_ID AND res.End_Date = cte.End_Date AND res.[Start_Date] = cte.[Start_Date] AND res.Frequency_ID = cte.Frequency_ID
	INNER JOIN UTILITY.CALENDAR AS cal ON cal.Calendar_Date = cte.End_Date
	WHERE 1=1
		AND (cte.nb <> cte.ct) OR (cte.nb = cte.ct AND nb_days >31) -- VPS 20190723 Delete periods larger than one month
		OR ( YEAR(cte.End_Date) = YEAR(GETDATE())					-- VPS 20190724 Remove last period if it is not full month
			AND MONTH(cte.End_Date) = MONTH(GETDATE()) 
			AND (cal.Month_End = 0 
			AND cal.Month_End_Business = 0))  
	;
	
	IF OBJECT_ID('tempdb..#temp_monthly') IS NOT NULL DROP TABLE #temp_monthly
	SELECT res.*, LEAD(res.End_Date) OVER (PARTITION BY res.Share_Class_ID ORDER BY res.End_Date DESC) AS dt
	INTO #temp_monthly
	FROM RESULTS.SRRI_RETURNS AS res
	WHERE 1=1	
		AND res.Frequency_ID = 5
	
	--DELETE FROM #temp_monthly WHERE dt IS NULL
	-- VPS 20190723 : remove obs that should not be used from RESULTS.SRRI_RETURNS
	DELETE res FROM RESULTS.SRRI_RETURNS AS res
	LEFT JOIN #temp_monthly AS t ON t.Share_Class_ID = res.Share_Class_ID AND t.End_Date = res.End_Date
	WHERE 1=1
		AND res.Frequency_ID = 5
		AND t.dt IS NULL

	UPDATE res
	SET res.[Start_Date] = t.dt
	FROM RESULTS.SRRI_RETURNS AS res	
	INNER JOIN #temp_monthly AS t ON t.Share_Class_ID = res.Share_Class_ID AND t.End_Date = res.End_Date
	
	
	-- compute OFFICIAL nav frequency total returns
	update H
	set H.share_class_total_return = t.share_class_total_return
		--,H.share_class_price_return = t.share_class_price_return
	from [RESULTS].[SRRI_RETURNS] H  
		inner join (
		select D.Share_Class_ID, D.[start_date], D.[end_date]
			   --,C.NAV_per_Share_in_Share_Ccy / P.NAV_per_Share_in_Share_Ccy - 1 as share_class_price_return,
			   --,(C.NAV_per_Share_in_Share_Ccy + isnull(F.flow_value_share_Ccy, 0)) / P.NAV_per_Share_in_Share_Ccy - 1 as share_class_total_return
			   ,(CAST(C.NAV_per_Share_in_Share_Ccy AS float) + isnull(CAST(F.flow_value_share_Ccy AS FLOAT), CAST(0 AS FLOAT))) / CAST(P.NAV_per_Share_in_Share_Ccy AS float) - 1.0 as share_class_total_return
		from [RESULTS].[SRRI_RETURNS] D 
			inner join HISTORY.NAVS C
			on C.NAV_Date = D.[end_date] AND C.Share_Class_ID = D.Share_Class_ID
			inner join HISTORY.NAVS P on P.NAV_Date = D.[start_date] AND P.Share_Class_ID = D.Share_Class_ID
			left join (select * from HISTORY.EXTERNAL_FLOWS where Flow_Type_id = 4) F 
			on D.[end_date] = F.flow_Date AND D.Share_Class_ID = F.Share_Class_ID) t
		on h.Share_Class_ID = t.Share_Class_ID and h.[start_date] = t.[start_date] and h.[end_date] = t.[end_date]



	-- delete history before last investment policy change

	delete from 
		RESULTS.SRRI_RETURNS 
	from 
		RESULTS.SRRI_RETURNS 
			INNER JOIN
		MASTER.SHARE_CLASSES s 
			ON RESULTS.SRRI_RETURNS.Share_Class_ID = s.Share_Class_ID
			inner join 
				(select p.Subfund_ID, p.Effective_Date
				from history.investment_policy p inner join
				(SELECT Subfund_ID, MAX(Effective_Date) AS dt
				FROM     HISTORY.INVESTMENT_POLICY
				GROUP BY Subfund_ID) h 
			on h.Subfund_ID = p.Subfund_ID and h.dt = p.Effective_Date) t
			on s.subfund_id = t.subfund_id
	where 
		RESULTS.SRRI_RETURNS.Start_Date < t.effective_date



	-- 1. fill history with share class filler

	insert into 
				RESULTS.SRRI_RETURNS
	SELECT		
				MASTER.SHARE_CLASSES.Share_Class_ID, R.Start_Date, R.End_Date, R.Frequency_ID, 
                R.Share_Class_Total_Return, 1 as is_filler
	FROM		
				RESULTS.SRRI_RETURNS r INNER JOIN MASTER.SHARE_CLASSES 
					ON R.Share_Class_ID = MASTER.SHARE_CLASSES.Share_Class_SRRI_Filler_ID
	where		R.End_Date <= isnull(MASTER.SHARE_CLASSES.Share_Class_end_date, @end_date)
				AND R.Start_Date >= @start_date
				and not exists (select * 
								from RESULTS.SRRI_RETURNS a
								where MASTER.SHARE_CLASSES.Share_Class_ID = a.Share_Class_ID
									and r.Start_Date = a.Start_Date
									and r.End_Date = a.End_Date)


	-- share class fillers need to be converted (subfund currency is assumed in case of hedged share classes)

	select  t.Share_Class_ID, t.Start_Date, t.End_Date, t.ccy_from, t.ccy_to
			,cast(0 as decimal(36, 14)) as fx_start_date
			,cast(0 as decimal(36, 14)) as fx_end_date
			,cast(0 as int) as proxy_id -- for later
			,cast(0 as decimal(36, 14)) as proxy_return -- for later
	into #temp_conversion
	from
		(SELECT RESULTS.SRRI_RETURNS.Share_Class_ID, RESULTS.SRRI_RETURNS.Start_Date, RESULTS.SRRI_RETURNS.End_Date, 
				RESULTS.SRRI_RETURNS.Share_Class_Total_Return, 
				case when SHARE_CLASSES_1.Share_Class_Ccy_Hedging_Percentage = 0 
					then SHARE_CLASSES_1.Share_Class_Currency_ID 
					else MASTER.SUBFUNDS.Subfund_Currency_ID 
				end as ccy_from,
				case when MASTER.SHARE_CLASSES.Share_Class_Ccy_Hedging_Percentage = 0 
					then MASTER.SHARE_CLASSES.Share_Class_Currency_ID 
					else MASTER.SUBFUNDS.Subfund_Currency_ID 
				end as ccy_to
		FROM    RESULTS.SRRI_RETURNS INNER JOIN
						  MASTER.SHARE_CLASSES ON RESULTS.SRRI_RETURNS.Share_Class_ID = MASTER.SHARE_CLASSES.Share_Class_ID INNER JOIN
						  MASTER.SHARE_CLASSES AS SHARE_CLASSES_1 ON MASTER.SHARE_CLASSES.Share_Class_SRRI_Filler_ID = SHARE_CLASSES_1.Share_Class_ID INNER JOIN
						  MASTER.SUBFUNDS ON MASTER.SHARE_CLASSES.Subfund_ID = MASTER.SUBFUNDS.Subfund_ID
		WHERE   RESULTS.SRRI_RETURNS.Is_Filler = 1) t
	where ccy_from <> ccy_to
	
	--ecr 2019-07-25
	UPDATE t
	SET t.[Start_Date] = IIF(cal.[Weekday]=6, DATEADD(DAY,-1,cal.Calendar_Date),DATEADD(DAY,-2,cal.Calendar_Date)) 
		,t.[End_Date] = IIF(cal2.[Weekday]=6, DATEADD(DAY,-1,cal2.Calendar_Date),DATEADD(DAY,-2,cal2.Calendar_Date)) 
	FROM #temp_conversion AS t
	INNER JOIN UTILITY.CALENDAR AS cal ON cal.Calendar_Date = t.[Start_Date]
	INNER JOIN UTILITY.CALENDAR AS cal2 ON cal2.Calendar_Date = t.[End_Date]
	WHERE 1=1
		AND (cal.[Weekday] IN (6,7) OR cal2.[Weekday] IN (6,7))


	update  #temp_conversion
	set		fx_start_date = HISTORY.FOREX.Value
	from	#temp_conversion inner join 
					HISTORY.FOREX ON #temp_conversion.ccy_from = HISTORY.FOREX.Currency_FROM_ID 
					AND #temp_conversion.ccy_to = HISTORY.FOREX.Currency_TO_ID 
					AND #temp_conversion.start_date = HISTORY.FOREX.Date
	WHERE   (HISTORY.FOREX.Field_ID = 7)

	update  #temp_conversion
	set		fx_end_date = HISTORY.FOREX.Value
	from	#temp_conversion inner join 
					HISTORY.FOREX ON #temp_conversion.ccy_from = HISTORY.FOREX.Currency_FROM_ID 
					AND #temp_conversion.ccy_to = HISTORY.FOREX.Currency_TO_ID 
					AND #temp_conversion.end_date = HISTORY.FOREX.Date
	WHERE   (HISTORY.FOREX.Field_ID = 7)

	update	RESULTS.SRRI_RETURNS
	set		Share_Class_Total_Return = (1 + r.Share_Class_Total_Return) * (t.fx_end_date / t.fx_start_date) - 1
	from	RESULTS.SRRI_RETURNS r inner join
				#temp_conversion t on t.Share_Class_ID = r.Share_Class_ID
				and t.Start_Date = r.Start_Date
				and t.End_Date = r.End_Date
				--20190806 ECR: avoiding set null
				AND (t.fx_end_date IS NOT NULL OR t.fx_start_date IS NOT NULL)


		-----------------------------------------------
		EXECUTE [dbo].[COMPUTE_BENCHMARKS_SRRI] @report_date
		-----------------------------------------------



	SELECT 
			MASTER.SHARE_CLASSES.Share_Class_ID, HISTORY.BENCHMARK_DATA.Start_Date, HISTORY.BENCHMARK_DATA.End_Date, 
                  HISTORY.BENCHMARKS.Benchmark_Type_ID, HISTORY.BENCHMARK_DATA.Benchmark_Return_EUR, 
				  case when MASTER.SHARE_CLASSES.Share_Class_Ccy_Hedging_Percentage = 0 
					then MASTER.SHARE_CLASSES.Share_Class_Currency_ID 
					else MASTER.SUBFUNDS.Subfund_Currency_ID 
				  end as ccy_to,
				  cast(0 as decimal(36, 14)) as FX_Return
	into 
			#temp_bmk
	FROM     
			HISTORY.BENCHMARK_DATA INNER JOIN
                  HISTORY.BENCHMARKS ON HISTORY.BENCHMARK_DATA.Benchmark_ID = HISTORY.BENCHMARKS.Benchmark_ID INNER JOIN
                  MASTER.SHARE_CLASSES ON HISTORY.BENCHMARKS.Subfund_ID = MASTER.SHARE_CLASSES.Subfund_ID inner join
				  master.subfunds on master.subfunds.Subfund_ID = MASTER.SHARE_CLASSES.Subfund_ID
	where	
			(HISTORY.BENCHMARKS.Benchmark_Type_ID = 1 or HISTORY.BENCHMARKS.Benchmark_Type_ID = 3)
			and master.subfunds.Subfund_SRRI = 1 and MASTER.SHARE_CLASSES.Share_Class_Is_Enabled = 1 
			and (MASTER.SHARE_CLASSES.Share_Class_End_Date is null or MASTER.SHARE_CLASSES.Share_Class_End_Date <= @end_date)
			

	UPDATE
			#temp_bmk
	SET     
		    FX_Return = HISTORY.FOREX.Value / FOREX_1.Value - 1
	FROM    
			#temp_bmk INNER JOIN
				HISTORY.FOREX ON #temp_bmk.ccy_to = HISTORY.FOREX.Currency_TO_ID AND #temp_bmk.End_Date = HISTORY.FOREX.Date INNER JOIN
				HISTORY.FOREX AS FOREX_1 ON #temp_bmk.ccy_to = FOREX_1.Currency_TO_ID AND #temp_bmk.Start_Date = FOREX_1.Date
	WHERE  
			(HISTORY.FOREX.Field_ID = 7) AND (HISTORY.FOREX.Currency_FROM_ID = 15) 
				AND (FOREX_1.Field_ID = 7) AND (FOREX_1.Currency_FROM_ID = 15)
	
	--20190806 ECR: avoiding set null
	DELETE FROM #temp_bmk
	WHERE FX_Return IS NULL


	-- 2. fill history with official benchmark

	insert into 
				RESULTS.SRRI_RETURNS
	SELECT		
				t.Share_Class_ID, t.Start_Date, t.End_Date, 1 as Frequency_ID, 
                t.Benchmark_Return, 1 as is_filler
	FROM		
				(SELECT Share_Class_ID, Start_Date, End_Date, 
						(1 + Benchmark_Return_EUR) * (1 + FX_Return) - 1 AS Benchmark_Return
				FROM     #temp_bmk
				where Benchmark_Type_ID = 1) t

			inner join

				(SELECT  r.Share_Class_ID, MIN(r.Start_Date) AS min_dt
				FROM     RESULTS.SRRI_RETURNS r 
						 inner join MASTER.SHARE_CLASSES 
						 on MASTER.SHARE_CLASSES.Share_Class_ID = r.Share_Class_ID
						 INNER JOIN (select p.Subfund_ID, p.Subfund_SRRI_Classification_ID
									from history.investment_policy p inner join
									(SELECT Subfund_ID, MAX(Effective_Date) AS dt
									FROM     HISTORY.INVESTMENT_POLICY
									GROUP BY Subfund_ID) a
									on p.Subfund_ID = a.subfund_id and p.Effective_Date = a.dt) t
						 ON MASTER.SHARE_CLASSES.Subfund_ID = t.Subfund_ID
				WHERE    t.Subfund_SRRI_Classification_ID = 1
				GROUP BY r.Share_Class_ID) d

			on d.Share_Class_ID = t.Share_Class_ID and t.Start_Date < d.min_dt and t.Start_Date > @start_date



	-- 3. fill history with SRRI benchmark

	insert into 
				RESULTS.SRRI_RETURNS
	SELECT		
				t.Share_Class_ID, t.Start_Date, t.End_Date, 1 as Frequency_ID, 
                t.Benchmark_Return, 1 as is_filler
	FROM		
				(SELECT Share_Class_ID, Start_Date, End_Date, 
						(1 + Benchmark_Return_EUR) * (1 + FX_Return) - 1 AS Benchmark_Return
				FROM     #temp_bmk
				where Benchmark_Type_ID = 3) t

			inner join

				(SELECT  r.Share_Class_ID, MIN(r.Start_Date) AS min_dt
				FROM     RESULTS.SRRI_RETURNS r 
						 inner join MASTER.SHARE_CLASSES 
						 on MASTER.SHARE_CLASSES.Share_Class_ID = r.Share_Class_ID
						 INNER JOIN (select p.Subfund_ID, p.Subfund_SRRI_Classification_ID
									from history.investment_policy p inner join
									(SELECT Subfund_ID, MAX(Effective_Date) AS dt
									FROM     HISTORY.INVESTMENT_POLICY
									GROUP BY Subfund_ID) a
									on p.Subfund_ID = a.subfund_id and p.Effective_Date = a.dt) t
						 ON MASTER.SHARE_CLASSES.Subfund_ID = t.Subfund_ID
				WHERE    t.Subfund_SRRI_Classification_ID = 1
				GROUP BY r.Share_Class_ID) d

			on d.Share_Class_ID = t.Share_Class_ID and t.Start_Date < d.min_dt and t.Start_Date > @start_date



	-- 4. fill history with proxy returns
	
	--ecr 20190527: data inputed on saturday and sunday can't be converted	
	UPDATE md
	SET md.[Date] = IIF(cal.[Weekday]=6, DATEADD(DAY,-1,md.[Date]),DATEADD(DAY,-2,md.[Date])) 
	FROM HISTORY.MARKET_DATA AS md
	INNER JOIN MASTER.INSTRUMENTS AS instr ON instr.Instrument_ID = md.Instrument_ID 
	INNER JOIN HISTORY.INVESTMENT_POLICY AS pol ON pol.Subfund_SRRI_Proxy_ID = instr.Instrument_ID
	INNER JOIN UTILITY.CALENDAR AS cal ON cal.Calendar_Date = md.[Date]
	WHERE 1=1
		AND md.Field_ID = 28
		AND cal.[Weekday] IN (6,7) 


	truncate table #temp_conversion

	
	insert into 
			#temp_conversion (Share_Class_ID, [start_date], [end_date], Proxy_ID, ccy_from, ccy_to)
	SELECT 
			MASTER.SHARE_CLASSES.Share_Class_ID, MAX(MARKET_DATA_1.Date) AS [start_date], HISTORY.MARKET_DATA.Date AS end_date, 
                  HISTORY.INVESTMENT_POLICY.Subfund_SRRI_Proxy_ID as Proxy_ID, MASTER.INSTRUMENTS.Instrument_Currency_ID as ccy_from, 
				  case when MASTER.SHARE_CLASSES.Share_Class_Ccy_Hedging_Percentage = 0 
					 then MASTER.SHARE_CLASSES.Share_Class_Currency_ID 
					 else MASTER.SUBFUNDS.Subfund_Currency_ID 
				  end as ccy_to
	FROM    
			HISTORY.MARKET_DATA INNER JOIN
					  HISTORY.MARKET_DATA AS MARKET_DATA_1 ON HISTORY.MARKET_DATA.Instrument_ID = MARKET_DATA_1.Instrument_ID AND 
					  HISTORY.MARKET_DATA.Field_ID = MARKET_DATA_1.Field_ID AND HISTORY.MARKET_DATA.Date > MARKET_DATA_1.Date INNER JOIN
					  HISTORY.INVESTMENT_POLICY ON HISTORY.MARKET_DATA.Instrument_ID = HISTORY.INVESTMENT_POLICY.Subfund_SRRI_Proxy_ID INNER JOIN
					  MASTER.SHARE_CLASSES ON HISTORY.INVESTMENT_POLICY.Subfund_ID = MASTER.SHARE_CLASSES.Subfund_ID INNER JOIN
					  MASTER.INSTRUMENTS ON HISTORY.MARKET_DATA.Instrument_ID = MASTER.INSTRUMENTS.Instrument_ID INNER JOIN
					  MASTER.SUBFUNDS ON MASTER.SHARE_CLASSES.Subfund_ID = MASTER.SUBFUNDS.Subfund_ID 
	WHERE	
			HISTORY.MARKET_DATA.Field_ID = 28 and MASTER.SHARE_CLASSES.Share_Class_Is_Enabled = 1 and MASTER.SUBFUNDS.Subfund_SRRI = 1
					and (MASTER.SHARE_CLASSES.Share_Class_End_Date is null or MASTER.SHARE_CLASSES.Share_Class_End_Date <= @end_date)
	GROUP BY 
			MASTER.SHARE_CLASSES.Share_Class_ID, HISTORY.MARKET_DATA.Date, HISTORY.INVESTMENT_POLICY.Subfund_SRRI_Proxy_ID, 
				  MASTER.INSTRUMENTS.Instrument_Currency_ID, 
				  case when MASTER.SHARE_CLASSES.Share_Class_Ccy_Hedging_Percentage = 0 
					 then MASTER.SHARE_CLASSES.Share_Class_Currency_ID 
					 else MASTER.SUBFUNDS.Subfund_Currency_ID 
				  end 

	update  #temp_conversion
	set		fx_start_date = HISTORY.FOREX.Value
	from	#temp_conversion inner join 
					HISTORY.FOREX ON #temp_conversion.ccy_from = HISTORY.FOREX.Currency_FROM_ID 
					AND #temp_conversion.ccy_to = HISTORY.FOREX.Currency_TO_ID 
					AND #temp_conversion.start_date = HISTORY.FOREX.Date
	WHERE   (HISTORY.FOREX.Field_ID = 7)

	update  #temp_conversion
	set		fx_end_date = HISTORY.FOREX.Value
	from	#temp_conversion inner join 
					HISTORY.FOREX ON #temp_conversion.ccy_from = HISTORY.FOREX.Currency_FROM_ID 
					AND #temp_conversion.ccy_to = HISTORY.FOREX.Currency_TO_ID 
					AND #temp_conversion.end_date = HISTORY.FOREX.Date
	WHERE   (HISTORY.FOREX.Field_ID = 7)

	update  #temp_conversion
	set		proxy_return = history.MARKET_DATA.Value 
	from	#temp_conversion inner join 
					history.MARKET_DATA on #temp_conversion.proxy_id = history.MARKET_DATA.Instrument_ID
					and #temp_conversion.end_Date = history.MARKET_DATA.Date 
	where	history.MARKET_DATA.Field_ID = 28
	
	--20190806 ECR: avoiding set null
	DELETE FROM #temp_conversion
	WHERE fx_start_date IS NULL OR fx_end_date IS NULL
	

	insert into 
				RESULTS.SRRI_RETURNS
	SELECT		
				t.Share_Class_ID, t.Start_Date, t.End_Date,
				-- 20190722 ECR: SRRI monthly 
				--, 1 as Frequency_ID, -- it was 3 before
				IIF(sf.SRRI_Frequency IS NULL, 3,5), --proxy returns are either entered weekly or monhtly
                t.proxy_return, 1 as is_filler
	FROM		
				(SELECT Share_Class_ID, Start_Date, End_Date, 
						(1 + proxy_return) * (fx_end_date / fx_start_date) - 1 AS proxy_return
				FROM     #temp_conversion) t

			inner join

				(SELECT  r.Share_Class_ID, MIN(r.Start_Date) AS min_dt
				FROM     RESULTS.SRRI_RETURNS r 
						 inner join MASTER.SHARE_CLASSES 
						 on MASTER.SHARE_CLASSES.Share_Class_ID = r.Share_Class_ID
						 INNER JOIN (select p.Subfund_ID, p.Subfund_SRRI_Classification_ID
									from history.investment_policy p inner join
									(SELECT Subfund_ID, MAX(Effective_Date) AS dt
									FROM     HISTORY.INVESTMENT_POLICY
									GROUP BY Subfund_ID) a
									on p.Subfund_ID = a.subfund_id and p.Effective_Date = a.dt) t
						 ON MASTER.SHARE_CLASSES.Subfund_ID = t.Subfund_ID
				WHERE    t.Subfund_SRRI_Classification_ID = 1
				GROUP BY r.Share_Class_ID) d

			on d.Share_Class_ID = t.Share_Class_ID and t.Start_Date < d.min_dt  and t.Start_Date > @start_date
	-- 20190722 ECR: SRRI monthly
	INNER JOIN MASTER.SHARE_CLASSES AS shc ON shc.Share_Class_ID = d.Share_Class_ID
	INNER JOIN MASTER.SUBFUNDS AS sf ON sf.Subfund_ID = shc.Subfund_ID

	
	---- compute annual returns by compounding
	--insert into [RESULTS].[SRRI_RETURNS] (Share_Class_ID, [start_date], [end_date], Frequency_ID, Share_Class_Total_Return)
	--SELECT Share_Class_ID, MIN([start_date]) AS [start_date], MAX([end_date]) AS [end_date], 8 as Frequency_ID,
	--	--EXP(SUM(LOG (1 + Share_Class_Price_Return))) - 1 AS Share_Class_Price_Return,
	--	EXP(SUM(LOG (1 + Share_Class_Total_Return))) - 1 AS Share_Class_Total_Return
	--	--,EXP(SUM(LOG (1 + Benchmark_Return))) - 1 AS Benchmark_Return
	--FROM [RESULTS].[SRRI_RETURNS]
	--where Frequency_ID < 8
	--GROUP BY Share_Class_ID, DATEPART(year, End_Date)


	---- compute monthly returns by compounding
	--insert into [RESULTS].[SRRI_RETURNS] (Share_Class_ID, [start_date], [end_date], Frequency_ID, Share_Class_Total_Return)
	--SELECT Share_Class_ID, MIN([start_date]) AS [start_date], MAX([end_date]) AS [end_date], 5 as Frequency_ID,
	--	--EXP(SUM(LOG (1 + Share_Class_Price_Return))) - 1 AS Share_Class_Price_Return,
	--	EXP(SUM(LOG (1 + Share_Class_Total_Return))) - 1 AS Share_Class_Total_Return
	--	--,EXP(SUM(LOG (1 + Benchmark_Return))) - 1 AS Benchmark_Return
	--FROM [RESULTS].[SRRI_RETURNS]
	--where Frequency_ID < 5
	--GROUP BY Share_Class_ID, DATEPART(year, End_Date), DATEPART(month, End_Date)



	-- compute weekly returns by compounding
	insert into [RESULTS].[SRRI_RETURNS] (Share_Class_ID, [start_date], [end_date], Frequency_ID, Share_Class_Total_Return)
	SELECT r.Share_Class_ID, MIN(r.[start_date]) AS [start_date], MAX(r.[end_date]) AS [end_date], 3 as return_frequency,
		--EXP(SUM(LOG (1 + r.Share_Class_Price_Return))) - 1 AS Share_Class_Price_Return,
		--EXP(SUM(LOG (1 + r.Share_Class_Total_Return))) - 1 AS Share_Class_Total_Return
		EXP(SUM(LOG (1 + CAST(r.Share_Class_Total_Return AS FLOAT)))) - 1 AS Share_Class_Total_Return
		--,EXP(SUM(LOG (1 + r.Benchmark_Return))) - 1 AS Benchmark_Return
	FROM [RESULTS].[SRRI_RETURNS] r inner join utility.calendar u
		on r.End_Date = u.Calendar_Date
	where r.Frequency_ID < 3
	GROUP BY r.Share_Class_ID, u.Cumulative_Week

	

	-- STORING CALCULATION IN REPORTS.SRRI

	truncate table reports.srri
	declare @cur_end_date date


	DECLARE  db_cursor CURSOR FOR  
	SELECT   
		UTILITY.CALENDAR.Calendar_Date 
	FROM 
		UTILITY.CALENDAR
	WHERE
		UTILITY.CALENDAR.Weekday = 5
		and UTILITY.CALENDAR.Calendar_Date > @start_date_4m
		and UTILITY.CALENDAR.Calendar_Date <= @end_date


	OPEN db_cursor   
	FETCH NEXT FROM db_cursor INTO @cur_end_date   


	WHILE @@FETCH_STATUS = 0   
	BEGIN   

			--insert into reports.srri ([Share_Class_ID],[Reference_Date],[Number_of_Returns],[SRRI_Volatility])
			--select 
			--	a.share_class_id, 
			--	@cur_end_date,
			--	a.c, 
			--	a.r
			--from
			--	(SELECT 
			--		SCs.Share_Class_ID
			--		--, max(End_Date) as d
			--		, COUNT(*) as c
			--		, stdev(rets.Share_Class_Total_Return) * sqrt(52) as r
			--	FROM (SELECT DISTINCT Share_Class_ID FROM RESULTS.SRRI_RETURNS) SCs 
			--		CROSS APPLY 
			--		(SELECT TOP (260) ret.Share_Class_Total_Return, 
			--			End_Date 
			--		FROM RESULTS.SRRI_RETURNS ret 
			--		where Scs.Share_Class_ID = ret.Share_Class_ID 
			--			AND ret.End_Date <= @cur_end_date AND Frequency_ID = 3 
			--		ORDER BY ret.End_Date DESC) rets
			--	GROUP BY SCs.Share_Class_ID) a 

			WITH top260 AS (
				SELECT *, ROW_NUMBER() 
				over (
					PARTITION BY Share_Class_ID
					order by End_Date DESC
				) AS RowNo 
				FROM RESULTS.SRRI_RETURNS
				-- 20190722 ECR: SRRI monthly 
				--WHERE  Frequency_ID = 3
				WHERE  Frequency_ID IN (3,5)  -- adding monthly frequency
					AND End_date <= @cur_end_date
			)

			INSERT INTO reports.srri ([Share_Class_ID],[Reference_Date],[Number_of_Returns],[SRRI_Volatility])
			SELECT 
				top260.Share_Class_ID
				,@cur_end_date
				, COUNT(*)
				-- 20190722 ECR: SRRI monthly 
				--, STDEV(Share_Class_Total_Return) * sqrt(52)
				, STDEV(Share_Class_Total_Return) * sqrt(IIF(sf.SRRI_Frequency IS NULL,52,12)  )
			FROM top260
			--20190722 ECR: MONTHLY SRRI
			INNER JOIN MASTER.SHARE_CLASSES AS shc ON shc.Share_Class_ID = top260.Share_Class_ID
			INNER JOIN MASTER.SUBFUNDS AS sf ON sf.Subfund_ID = shc.Subfund_ID
			WHERE 1 = 1
				-- 20190722 ECR: SRRI monthly 
				--AND RowNo <= 260
				AND RowNo <= IIF(sf.SRRI_Frequency IS NULL,260,60)  
			-- 20190722 ECR: SRRI monthly 
			--GROUP BY Share_Class_ID
			GROUP BY top260.Share_Class_ID, sf.SRRI_Frequency
			ORDER BY top260.Share_Class_ID

		    FETCH NEXT FROM db_cursor INTO @cur_end_date  

	END   


	CLOSE db_cursor   
	DEALLOCATE db_cursor
	
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
	-- VPS 20190724 For monthly SRRI keep only last friday of each month for computation date.
	IF OBJECT_ID('tempdb..#srri_friday') IS NOT NULL DROP TABLE #srri_friday
	;WITH CTE AS (SELECT cal.Calendar_Date, ROW_NUMBER() OVER (PARTITION BY cal.[YEAR], cal.[Month] ORDER BY cal.[Calendar_Date]) AS nb 
		,COUNT(cal.Calendar_Date) OVER (PARTITION BY cal.[YEAR], cal.[Month] ) AS ct
		FROM UTILITY.CALENDAR AS cal
		WHERE 1=1
			AND cal.[Weekday] = 5
			AND cal.Calendar_Date<= CONVERT(DATE,DATEADD(MONTH, DATEDIFF(MONTH, -1, GETDATE())-1, -1),103)
			AND cal.Calendar_Date>= DATEADD(YEAR,-5,GETDATE())	) 

	SELECT cte.* 
	INTO #srri_friday
	FROM CTE AS cte	
	WHERE cte.nb = cte.ct
	;

	DELETE FROM srri
	FROM REPORTS.SRRI AS srri
	INNER JOIN MASTER.SHARE_CLASSES AS shc ON shc.Share_Class_ID = srri.Share_Class_ID 
	INNER JOIN MASTER.SUBFUNDS AS sf ON sf.Subfund_ID = shc.Subfund_ID
	LEFT JOIN #srri_friday AS cal ON cal.Calendar_Date = srri.Reference_Date
	WHERE 1=1
		AND sf.SRRI_Frequency IS NOT NULL
		AND cal.Calendar_Date IS NULL
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------	

	

	UPDATE	REPORTS.SRRI
	SET     SRRI_Volatility = u.Annual_Volatility_Limit 
	from	REPORTS.SRRI inner join
			(SELECT MASTER.SHARE_CLASSES.Share_Class_ID, MASTER.SHARE_CLASSES.Share_Class_start_date, HISTORY.ABSOLUTE_RETURN_FUNDS.Annual_Volatility_Limit
			FROM     MASTER.SHARE_CLASSES INNER JOIN HISTORY.INVESTMENT_POLICY
					ON MASTER.SHARE_CLASSES.Subfund_ID = HISTORY.INVESTMENT_POLICY.Subfund_ID
				 inner join (SELECT Subfund_ID, MAX(Effective_Date) AS dt
						FROM     HISTORY.INVESTMENT_POLICY
						WHERE  Subfund_SRRI_Classification_ID = 2
						GROUP BY Subfund_ID) p 
					ON p.Subfund_ID = HISTORY.INVESTMENT_POLICY.Subfund_ID 
					and p.dt = HISTORY.INVESTMENT_POLICY.Effective_Date
				 INNER JOIN HISTORY.ABSOLUTE_RETURN_FUNDS 
					ON MASTER.SHARE_CLASSES.Share_Class_ID = HISTORY.ABSOLUTE_RETURN_FUNDS.Share_Class_ID) u
			 on u.Share_Class_ID = REPORTS.SRRI.Share_Class_ID


	UPDATE	REPORTS.SRRI
	SET     SRRI_Volatility = case when u.Annual_Volatility_Limit < REPORTS.SRRI.SRRI_Volatility
								then REPORTS.SRRI.SRRI_Volatility 
								else u.Annual_Volatility_Limit end,
			Number_of_Returns = 0
	from	REPORTS.SRRI inner join
			(SELECT MASTER.SHARE_CLASSES.Share_Class_ID, MASTER.SHARE_CLASSES.Share_Class_start_date, HISTORY.ABSOLUTE_RETURN_FUNDS.Annual_Volatility_Limit
			FROM     MASTER.SHARE_CLASSES INNER JOIN HISTORY.INVESTMENT_POLICY
					ON MASTER.SHARE_CLASSES.Subfund_ID = HISTORY.INVESTMENT_POLICY.Subfund_ID
				 inner join (SELECT Subfund_ID, MAX(Effective_Date) AS dt
						FROM     HISTORY.INVESTMENT_POLICY
						WHERE  Subfund_SRRI_Classification_ID = 2
						GROUP BY Subfund_ID) p 
					ON p.Subfund_ID = HISTORY.INVESTMENT_POLICY.Subfund_ID 
					and p.dt = HISTORY.INVESTMENT_POLICY.Effective_Date
				 INNER JOIN HISTORY.ABSOLUTE_RETURN_FUNDS 
					ON MASTER.SHARE_CLASSES.Share_Class_ID = HISTORY.ABSOLUTE_RETURN_FUNDS.Share_Class_ID) u
			 on u.Share_Class_ID = REPORTS.SRRI.Share_Class_ID
	where	 Number_of_Returns <> 0 and u.Share_Class_start_date > DATEADD(mm, -60, @end_date)



	UPDATE	 REPORTS.SRRI
	SET      SRRI = UTILITY.SRRI_RISK_CLASSES.SRRI
	FROM     REPORTS.SRRI INNER JOIN UTILITY.SRRI_RISK_CLASSES 
				ON REPORTS.SRRI.SRRI_Volatility >= UTILITY.SRRI_RISK_CLASSES.Min_Volatility  
				AND REPORTS.SRRI.SRRI_Volatility < UTILITY.SRRI_RISK_CLASSES.Max_Volatility


	
	--insert into	utility.warnings (Table_Name, Field_Name, Field_Value, Warning_Message)
	--SELECT		'REPORTS.SRRI', 'Share_Class_ID', REPORTS.SRRI.Share_Class_ID, 'SRRI returns are only ' + cast(max(Number_of_Returns) as nvarchar(3))
	--FROM		REPORTS.SRRI INNER JOIN
	--			MASTER.SHARE_CLASSES s ON s.Share_Class_ID = REPORTS.SRRI.Share_Class_ID	
	--WHERE		Number_of_Returns > 0 and Number_of_Returns < 260
	--			and Reference_Date >= eomonth(@report_date,-4)
	--			and s.Share_Class_Is_Enabled = 1
	--			and (s.Share_Class_End_Date is null or (s.Share_Class_End_Date is not null and s.Share_Class_End_Date> eomonth(@report_date,-4)))
	--group by	REPORTS.SRRI.Share_Class_ID

	EXEC dbo.INTERFACE_VIEW_SRRI_COMPOSITION NULL,@report_date

	insert into	utility.warnings (Table_Name, Field_Name, Field_Value, Warning_Message)
	SELECT		'REPORTS.SRRI', 'Share_Class_ID', TEMP.[SRRI_COMP].SHC, 'SRRI returns are only ' + cast(wk_TOTAL as nvarchar(3))
	FROM		TEMP.[SRRI_COMP] 	


	insert into [UTILITY].[APP_LOGS] ([EntryID], [Type] , [EntryDate] ,[ApplicationName] )
	values (newid(), 'ProcedureEnd', getdate(), 'COMPUTE_SRRI' )


end try

begin catch

	insert into [UTILITY].[APP_LOGS] ([EntryID], [Type] , [EntryDate] ,[ApplicationName] ,[ExceptionMessage] ,[Message])
	values (newid(), 'Error', getdate(), ERROR_PROCEDURE(), ERROR_LINE() ,ERROR_MESSAGE())

end catch
    
END

