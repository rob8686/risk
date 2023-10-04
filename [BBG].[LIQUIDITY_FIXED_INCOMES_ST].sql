/*    ==Scripting Parameters==

    Source Server Version : SQL Server 2012 (11.0.6251)
    Source Database Engine Edition : Microsoft SQL Server Standard Edition
    Source Database Engine Type : Standalone SQL Server

    Target Server Version : SQL Server 2012
    Target Database Engine Edition : Microsoft SQL Server Standard Edition
    Target Database Engine Type : Standalone SQL Server
*/

USE [METIS2]
GO

/****** Object:  StoredProcedure [BBG].[LIQUIDITY_FIXED_INCOMES_ST]    Script Date: 22-05-2023 17:15:38 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO





CREATE PROCEDURE [BBG].[LIQUIDITY_FIXED_INCOMES_ST]
@EOM_Business DATE,
@Subfund_ID INT = NULL
AS
BEGIN
	
	
-- SET NOCOUNT ON added to prevent extra result sets from
-- interfering with SELECT statements.
SET NOCOUNT ON;
SET ARITHABORT ON;
begin try

	
	insert into [UTILITY].[APP_LOGS] ([EntryID], [Type] , [EntryDate] ,[ApplicationName] )
	values (newid(), 'ProcedureStart', getdate(), 'LIQUIDITY_FIXED_INCOMES_ST' )

    --DECLARE @EOM_Business DATE = '2020-05-29'
	DECLARE @SF_ID INT = @Subfund_ID
	DECLARE @report_date DATE = @EOM_Business
    DECLARE @Asset_Class_ID INT = 2
	
	DECLARE @BASE_PARTICIPATION_RATE DECIMAL(36,14) = 0.6--0.25 --0.6-- Base Participation Rate for Bonds

	DECLARE @G10_Curr TABLE (Currency_ID INT)

	INSERT INTO @G10_Curr VALUES(15)
	INSERT INTO @G10_Curr VALUES(52)
	INSERT INTO @G10_Curr VALUES(7)
	INSERT INTO @G10_Curr VALUES(25)
	INSERT INTO @G10_Curr VALUES(44)
	INSERT INTO @G10_Curr VALUES(8)
	INSERT INTO @G10_Curr VALUES(16)
    
    DECLARE @RATING_LEVELS TABLE(Rating_ID INT ,Rating varchar(5),  Lower_Level_ID INT)
    INSERT INTO @RATING_LEVELS VALUES
    -- (0,'Sink', NULL),
    (1,'NR',  1),
    (2,'NA',  2),
    (3,'D2',  3),
    (4,'D1',  3),
    (5,'HY2', 4),
    (6,'HY1', 5),
    (7,'IG2', 6),
    (8,'IG1', 7)

	--pb 20230213: Blocked

 --   DECLARE @MARKIT_LIQUIDITY_RATING TABLE(Rating int, haircut DECIMAL(36,14), Time_To_Liquidate int, Higher_level_ID INT)
 --   INSERT INTO @MARKIT_LIQUIDITY_RATING VALUES
	--(1, 0.01, 5, 2)
	--,(2, 0.05, 15, 3)
	--,(3, 0.07, 20, 4)
	--,(4, 0.1, 30, 5)
	--,(5, 0.15, 90, 5)

	--DECLARE @Scenario_Loan_Param_Overwrites TABLE(Scenario_ID int, Liquidity_Rating int, haircut DECIMAL(36,14), Time_To_Liquidate Int)
	--INSERT INTO @Scenario_Loan_Param_Overwrites VALUES
	--(19, 1, 0.05, 10)
	--,(19, 2, 0.1, 30)
	--,(19, 3, 0.15, 40)
	--,(19, 4, 0.2, 60)
	--,(19, 5, 0.3, 180)
	--,(20, 1, 0.07, 15)
	--,(20, 2 ,0.14, 40)
	--,(20, 3, 0.2, 60)
	--,(20, 4, 0.27, 90)
	--,(20, 5, 0.4, 210)

	--pb 20230213: The revised haircut and score have been implemented

	DECLARE @MARKIT_LIQUIDITY_RATING TABLE(Rating int, haircut DECIMAL(36,14), Time_To_Liquidate int, Higher_level_ID INT)
    INSERT INTO @MARKIT_LIQUIDITY_RATING VALUES
	(1, 0.03, 4, 2)
	,(2, 0.05, 10, 3)
	,(3, 0.09, 22, 4)
	,(4, 0.15, 49, 5)
	,(5, 0.24, 109, 5)

	DECLARE @Scenario_Loan_Param_Overwrites TABLE(Scenario_ID int, Liquidity_Rating int, haircut DECIMAL(36,14), Time_To_Liquidate Int)
	INSERT INTO @Scenario_Loan_Param_Overwrites VALUES
	(1, 1, 0.03, 4)
	,(1, 2, 0.05, 10)
	,(1, 3, 0.09, 22)
	,(1, 4, 0.15, 49)
	,(1, 5, 0.24, 109)
	,(19, 1, 0.05, 7)
	,(19, 2, 0.08, 15)
	,(19, 3, 0.13, 33)
	,(19, 4, 0.22, 74)
	,(19, 5, 0.37, 164)
	,(20, 1, 0.06, 9)
	,(20, 2 ,0.11, 19)
	,(20, 3, 0.17, 43)
	,(20, 4, 0.29, 96)
	,(20, 5, 0.48, 213)

	IF OBJECT_ID('tempdb..#scenarios') IS NOT NULL DROP TABLE #scenarios

	SELECT  
		Scenario_ID
		, Description
		, Asset_Class_Id
		, Asset_Class_Describtion
		, ISNULL([1], 0) AS Avg_Spread_Shift
		, ISNULL([2], 0) AS Volatility_Shift
		, ISNULL([3], 0) AS Haircut_Stress_Shift
		, ISNULL([4], 0) AS Delta_Shift
        , ISNULL([5], 0) AS Rating_Downgrade_Factor
        , ISNULL([6], 0) AS Ownership_Shift
		, ISNULL([7], 0) AS Participation_Rate_shift
		, ISNULL([8], 0) AS Avg_Daily_Traded_Volume_Shift
		, ISNULL([9], 0) AS Loan_Haircut_Shift
		, ISNULL([10], 0) AS Loan_Time_To_Liquidate_Shift
		, ISNULL([11], 0) AS Loan_Liquidity_Score_Downgrade_Factor
	INTO #scenarios
	FROM (        
	SELECT 
		tsc.Scenario_ID
		, tsc.[Description]
		,las.Asset_Class_ID
		,lst.Parameter_ID
		,lst.Value
		,las.Description as Asset_Class_Describtion 
	FROM LIST.LIQUIDITY_STRESS_TEST_SCENARIO tsc
    CROSS JOIN list.LIQUIDITY_ASSET_CLASS las
	LEFT JOIN BBG.LIQUIDITY_STRESS_TEST_PARAMETERS lst ON tsc.Scenario_ID = lst.Scenario_ID AND lst.Asset_Class_ID = las.Asset_Class_ID
	WHERE 1=1
		AND tsc.Is_active = 1
        AND las.Asset_Class_ID = @Asset_Class_ID
	) as t
	PIVOT
	(
		MIN(Value)
		FOR Parameter_ID in ([1], [2], [3], [4], [5], [6], [7], [8], [9], [10], [11])
	) as pt

    -- SELECT *
    -- FROM #scenarios

    IF OBJECT_ID('tempdb..#ratings_downgrade') IS NOT NULL DROP TABLE #ratings_downgrade
    ;WITH ratings AS
    (
    SELECT 
        sc.Scenario_ID
        , sc.Rating_Downgrade_Factor
        , rl.Rating_ID 
        , rl.Rating
        , rl.Lower_Level_ID
        , 0 AS rec_level
        , rl.Rating_ID AS Rating_ID_Stress
        , rl.Rating AS Rating_Downgraded
    FROM @RATING_LEVELS rl
    CROSS JOIN #scenarios sc
    UNION ALL
    SELECT 
        r.Scenario_ID
        , r.Rating_Downgrade_Factor
        , rlc.Rating_ID
        , rlc.Rating
        , rlc.Lower_Level_ID
        , rec_level + 1
        , r.Rating_ID_Stress
        , r.Rating_Downgraded
    FROM @RATING_LEVELS rlc
    INNER JOIN ratings r ON r.Rating_ID = rlc.Lower_Level_ID
    WHERE 1=1
        AND rec_level < Rating_Downgrade_Factor
    )
    SELECT Scenario_ID, Rating_Downgrade_Factor, Rating, Rating_Downgraded
    INTO #ratings_downgrade
    FROM ratings
    WHERE 1=1
    AND rec_level = Rating_Downgrade_Factor
    ;

    IF OBJECT_ID('tempdb..#Loans_Liq_Scores') IS NOT NULL DROP TABLE #Loans_Liq_Scores
    ;WITH ratings AS
    (
    SELECT 
        sc.Scenario_ID
        , sc.Loan_Liquidity_Score_Downgrade_Factor
        , rl.Rating
        , rl.Higher_level_ID
        , 0 AS rec_level
		, rl.Rating AS Rating_Stress
        , rl.Rating AS Rating_Downgraded
    FROM @MARKIT_LIQUIDITY_RATING rl
    CROSS JOIN #scenarios sc
    UNION ALL
    SELECT 
        r.Scenario_ID
        , r.Loan_Liquidity_Score_Downgrade_Factor
        , rlc.Rating
        , rlc.Higher_level_ID
        , rec_level + 1
        , r.Rating_Stress
        , r.Rating_Downgraded
    FROM @MARKIT_LIQUIDITY_RATING rlc
    INNER JOIN ratings r ON r.Rating = rlc.Higher_level_ID
    WHERE 1=1
        AND rec_level < Loan_Liquidity_Score_Downgrade_Factor
    )
    SELECT Scenario_ID, Loan_Liquidity_Score_Downgrade_Factor, Rating, Rating_Downgraded
    INTO #Loans_Liq_Scores
    FROM ratings
    WHERE 1=1
    AND rec_level = Loan_Liquidity_Score_Downgrade_Factor
    ;


	IF OBJECT_ID('tempdb..#base') IS NOT NULL DROP TABLE #base

	SELECT
		sc.*
		,s.[Nav_Date]
		,sf.Subfund_CA_ID
		,s.[Subfund_ID]
		,s.[Instrument_ID]
		,ins.Instrument_Description
		,ins.Instrument_Bloomberg_Code
		,ins.Instrument_ISIN
		,s.Liquidity_Asset_Class_ID
		,[Spread_Bid_Ask] * (1 + sc.Avg_Spread_Shift) AS [Spread_Bid_Ask] 
		,[Volatility_Mid_Bid_Ask] * SQRT(252) * (1 + sc.Volatility_Shift) AS [Volatility_Mid_Bid_Ask] --Annualized
		, s.Underlying_PX_Volume
		, CASE
			WHEN ins.Instrument_Currency_ID = 42 -- Any security denominated in RUB
				OR ins.Instrument_ISIN LIKE 'RU%' -- RU ISIN
				OR rs.ISIN IS NOT NULL -- Sec in specified list
				THEN 366
			WHEN ins.Instrument_Currency_ID = 83 THEN 150 --, due to lack of liquidity in the Nigerian market, we force the number of days to settle to 150 days
			WHEN lr.Markit_Liquidity_Score IS NOT NULL AND ins.Instrument_Subtype_ID = 9 THEN 3 -- loans are settling in T+3
			ELSE COALESCE(s.[Days_To_Settle], cds.Days_To_Settle) 
		  END AS [Days_To_Settle] 
		, ins.Instrument_Maturity
		, (DATEDIFF(DAY,s.Nav_Date, ins.Instrument_Maturity)/365.25) as Maturity_in_Year
		, r.[Rating_Downgraded] AS Rating
		, s.Is_Callable
		, s.Market_Sector_Des
		, ins.Instrument_Currency_ID
		, s.Issue_Dt
		, p.Quantity/ ins.Instrument_Contract_Size_Factor AS Quantity
		, p.Market_Value_Subfund_Ccy
		, (mv.Avg_Daily_Traded_Volume_30D * (1 + sc.Avg_Daily_Traded_Volume_Shift)) * (@BASE_PARTICIPATION_RATE + sc.Participation_Rate_shift) AS Applicable_Daily_Volume
		, (mvc.Volume_Country * (1 + sc.Avg_Daily_Traded_Volume_Shift)) * (@BASE_PARTICIPATION_RATE + sc.Participation_Rate_shift) AS Applicable_Daily_Volume_Country
		, ((ABS(p.Quantity)/ ins.Instrument_Contract_Size_Factor) / Amt_Outstanding) * (1 + sc.Ownership_Shift) as [Ownership]
		, ast.Asset_Type_ID
		, lr.Markit_Liquidity_Score
		, IIF(lr.Markit_Liquidity_Score IS NOT NULL AND ins.Instrument_Subtype_ID = 9, 1, 0) AS Loan_Indicator
		, CASE 
			WHEN Spread_Bid_Ask * (1 + sc.Avg_Spread_Shift) IS NULL THEN 10
			WHEN Spread_Bid_Ask * (1 + sc.Avg_Spread_Shift) < 0.005 THEN 10
			WHEN Spread_Bid_Ask * (1 + sc.Avg_Spread_Shift) < 0.01 THEN 9
			WHEN Spread_Bid_Ask * (1 + sc.Avg_Spread_Shift) < 0.02 THEN 8
			WHEN Spread_Bid_Ask * (1 + sc.Avg_Spread_Shift) < 0.03 THEN 7
			ELSE 6
		END AS init_Score
		, CASE
			WHEN ins.Instrument_Currency_ID = 42 -- Any security denominated in RUB
				OR ins.Instrument_ISIN LIKE 'RU%' -- RU ISIN
				OR rs.ISIN IS NOT NULL -- Sec in specified list
				THEN 1
				ELSE 0
		END AS Iliquid_Indicator
	INTO #base
	FROM [METIS2].[TEMP].[LIQUIDITY_EXPORT_STAGING] s
	INNER JOIN MASTER.SUBFUNDS sf on sf.Subfund_ID = s.Subfund_ID
	INNER JOIN HISTORY.PORTFOLIOS p  on p.Subfund_ID = s.Subfund_ID AND p.Instrument_ID = s.Instrument_ID AND p.Nav_Date = s.Nav_Date AND sf.Subfund_Export_Type = p.Look_Through
	INNER JOIN MASTER.INSTRUMENTS ins on ins.Instrument_ID = s.Instrument_ID
	LEFT JOIN LIST.ASSET_SUBTYPES ast On ast.Asset_Subtype_ID = ins.Instrument_Subtype_ID
	LEFT JOIN UTILITY.COUNTRY_DAYS_TO_SETTLE cds ON cds.Country_ID = ins.Instrument_Country_ID
	LEFT JOIN UTILITY.LIQUIDITY_SANCTIONED_ISINS rs ON rs.ISIN = ins.Instrument_ISIN
	LEFT JOIN HISTORY.MARKIT_VOLUMES mv ON mv.ISIN = ins.Instrument_ISIN AND EOMonth(mv.[Date]) = EOMonth(s.Nav_Date) 
	--LEFT JOIN BBG.MDO_LIQUIDITY_RATING r ON r.Bloomberg_code = ins.Instrument_Bloomberg_Code AND r.[Date] = @report_date
	LEFT JOIN HISTORY.MARKIT_VOLUMES_COUNTRY mvc ON mvc.[Date] = eomonth(@report_date) AND mvc.Country_ID = ins.Instrument_Country_ID 
		AND DATEDIFF(d, @report_date, ins.Instrument_Maturity) BETWEEN mvc.bd_min AND mvc.bd_max
		AND (RIGHT(ins.Instrument_Bloomberg_Code, 4)  = 'Govt' OR s.Market_Sector_Des = 'Govt')   --Government Bond: bloomberg code and market_sector_desc are not always consistent
    INNER JOIN #scenarios sc ON 1=1
    LEFT JOIN
    (
        SELECT rd.Scenario_ID, r.Bloomberg_code, rd.Rating_Downgraded
        FROM BBG.MDO_LIQUIDITY_RATING r
        LEFT JOIN #ratings_downgrade rd ON rd.Rating = r.[Value]
        WHERE 1=1
            AND r.[Date] = @report_date 
    ) r ON r.Bloomberg_code = ins.Instrument_Bloomberg_Code AND sc.Scenario_ID = r.Scenario_ID
	LEFT JOIN
	(
		SELECT sd.Scenario_ID, ls.Instrument_Id, sd.Rating_Downgraded AS Markit_Liquidity_Score
		FROM BBG.MARKIT_LIQUIDITY_SCORES ls
		LEFT JOIN #Loans_Liq_Scores sd ON sd.Rating = ls.Markit_Liquidity_Score
        WHERE 1=1
            AND EOMONTH(ls.[Date]) = EOMONTH(@report_date)
	) lr ON s.Instrument_ID = lr.Instrument_ID AND sc.Scenario_ID = lr.Scenario_ID
	WHERE 1=1
		AND (s.Subfund_ID = @SF_ID OR @SF_ID IS NULL)
		AND (s.Liquidity_Asset_Class_ID IN (2,3))
		-- AND ins.Instrument_ID = 689816
		-- AND sf.Subfund_ID = 1
        --AND sc.Scenario_ID = 1

	IF OBJECT_ID('tempdb..#score_effects') IS NOT NULL DROP TABLE #score_effects

	SELECT
		b.*
		, CASE
			WHEN [Ownership] < 0.0001 THEN 1
			WHEN [Ownership] < 0.005 THEN 0
			WHEN [Ownership] < 0.01 THEN -0.2
			WHEN [Ownership] < 0.02 THEN -0.5
			WHEN [Ownership] < 0.05 THEN -1
			ELSE -2
		END AS Ownership_effect
		, CASE
			WHEN Maturity_in_Year < 1 THEN 0
			WHEN Maturity_in_Year < 3 THEN -0.2
			WHEN Maturity_in_Year < 5 THEN -0.5
			WHEN Maturity_in_Year < 10 THEN -0.8
			ELSE -1
		END AS Maturity_Effect
		, CASE 
			WHEN Maturity_in_Year < 1 THEN 0
			WHEN Maturity_in_Year < 3 THEN -0.5
			ELSE -1
		END AS Duration_Effect
		, CASE Rating
			WHEN 'NA' THEN 0
			WHEN 'IG1' THEN 0
			WHEN 'IG2' THEN 0
			WHEN 'HY1' THEN -0.2
			WHEN 'HY2' THEN -0.2
			ELSE -0.5
		END AS Rating_Effect
		, CASE Is_Callable
			WHEN  1 THEN 0
			ELSE -0.2
		END AS Call_Effect
		, CASE
			WHEN Volatility_Mid_Bid_Ask < 0.005 THEN 0
			WHEN Volatility_Mid_Bid_Ask < 0.01 THEN -0.2
			WHEN Volatility_Mid_Bid_Ask < 0.02 THEN -0.5
			WHEN Volatility_Mid_Bid_Ask < 0.05 THEN -0.8
			WHEN Volatility_Mid_Bid_Ask < 0.1 THEN -1
			ELSE -1.5
		END AS Vol_Effect
	INTO #score_effects
	FROM #base b

	IF OBJECT_ID('tempdb..#final_Score') IS NOT NULL DROP TABLE #final_Score

	SELECT *
		, CASE WHEN init_Score + Ownership_effect + Maturity_Effect + Duration_Effect + Rating_Effect + Call_Effect + Vol_Effect < 0 
				THEN 0
			WHEN init_Score + Ownership_effect + Maturity_Effect + Duration_Effect + Rating_Effect + Call_Effect + Vol_Effect < 10
				THEN init_Score + Ownership_effect + Maturity_Effect + Duration_Effect + Rating_Effect + Call_Effect + Vol_Effect
			ELSE 10
		END AS Liquidity_Score
	INTO #final_Score
	FROM #score_effects
	WHERE 1=1

	IF OBJECT_ID('tempdb..#fi_haircuts') IS NOT NULL DROP TABLE #fi_haircuts

	SELECT 
		fs.* 
		, CASE 
			WHEN Loan_Indicator = 1--Markit_Liquidity_Score IS NOT NULL AND Instrument_Subtype_ID = 9
			THEN 
			--pb 20230213: Blocked
				--(
				--CASE Markit_Liquidity_Score
				--WHEN 1 THEN COALESCE(ovr.haircut, 0.0)
				--WHEN 2 THEN COALESCE(ovr.haircut, 0.05)
				--WHEN 3 THEN COALESCE(ovr.haircut, 0.07)
				--WHEN 4 THEN COALESCE(ovr.haircut, 0.1)
				--WHEN 5 THEN COALESCE(ovr.haircut, 0.15)
				--END
				--)

				--hj 20221024: New changes to be implemeted
				--pb 20230213: The revised haircut and score have been implemented

				(
				CASE Markit_Liquidity_Score
				WHEN 1 THEN COALESCE(ovr.haircut, 0.03)
				WHEN 2 THEN COALESCE(ovr.haircut, 0.05)
				WHEN 3 THEN COALESCE(ovr.haircut, 0.09)
				WHEN 4 THEN COALESCE(ovr.haircut, 0.15)
				WHEN 5 THEN COALESCE(ovr.haircut, 0.24)
				END
				)
			WHEN Market_Sector_Des IN ('Corp', 'Govt')
			THEN (
				CASE
					WHEN Liquidity_Score < 1 THEN 0.5
					WHEN Liquidity_Score < 2 THEN 0.45
					WHEN Liquidity_Score < 3 THEN 0.4
					WHEN Liquidity_Score < 4 THEN 0.35
					WHEN Liquidity_Score < 5 THEN 0.3
					WHEN Liquidity_Score < 6 THEN 0.25
					WHEN Liquidity_Score < 7 THEN 0.2
					WHEN Liquidity_Score < 8 THEN 0.15
					WHEN Liquidity_Score < 9 THEN 0.1
					WHEN Liquidity_Score < 10 THEN 0.05
					WHEN Liquidity_Score >= 10 THEN 0.0
				END
			)
			ELSE (
				CASE
					WHEN Liquidity_Score < 1 THEN 0.6
					WHEN Liquidity_Score < 2 THEN 0.5
					WHEN Liquidity_Score < 3 THEN 0.45
					WHEN Liquidity_Score < 4 THEN 0.4
					WHEN Liquidity_Score < 5 THEN 0.35
					WHEN Liquidity_Score < 6 THEN 0.3
					WHEN Liquidity_Score < 7 THEN 0.25
					WHEN Liquidity_Score < 8 THEN 0.20
					WHEN Liquidity_Score < 9 THEN 0.1
					WHEN Liquidity_Score < 10 THEN 0.05
					WHEN Liquidity_Score >= 10 THEN 0.0
				END
			)
			END AS haircut
	INTO #fi_haircuts
	FROM #final_Score fs
	LEFT JOIN @Scenario_Loan_Param_Overwrites ovr ON ovr.Scenario_ID = fs.Scenario_ID AND ovr.Liquidity_Rating = fs.Markit_Liquidity_Score

	IF OBJECT_ID('tempdb..#haircuts') IS NOT NULL DROP TABLE #haircuts
	SELECT
		h.*
		, ee.Liquidation_Cost AS EQ_Liquidation_Cost
		, hmk.[Value] AS Delta
		, CASE
			WHEN Iliquid_Indicator =1 THEN 0.0
			-- for convertibles without volume of underlying apply fixed income methodology only
			WHEN ee.Instrument_ID IS NOT NULL AND (h.Underlying_PX_Volume IS NULL OR  h.Underlying_PX_Volume = 0) 
			THEN (hmk.[Value] * (1+Delta_Shift) )* ee.Liquidation_Cost + (1-hmk.[Value] * (1+Delta_Shift)) * h.haircut
		ELSE haircut
		END As final_haircut
	INTO #haircuts
	FROM #fi_haircuts h
	LEFT JOIN BBG.CONVERTIBLES_EQUITY_ELEMENT_ST ee ON  ee.NAV_Date = h.Nav_Date 
		AND ee.Subfund_ID = h.Subfund_ID 
		AND ee.Instrument_ID = h.Instrument_ID 
		AND h.Liquidity_Asset_Class_ID = 3
        AND ee.Scenario_ID = h.Scenario_ID
	LEFT JOIN HISTORY.MARKET_DATA hmk ON hmk.Instrument_ID= h.Instrument_ID ANd hmk.[Date] = h.Nav_Date AND Field_ID = 5

	IF OBJECT_ID('tempdb..#main') IS NOT NULL DROP TABLE #main

	SELECT 
		h.*
		, CASE
			WHEN Iliquid_Indicator =1 THEN Market_Value_Subfund_Ccy -- Full recovery at 366
			WHEN Quantity > 0
				THEN Market_Value_Subfund_Ccy * (1- final_haircut - Haircut_Stress_Shift)
			ELSE Market_Value_Subfund_Ccy * (1 + final_haircut + Haircut_Stress_Shift)
		END as Recovered_Mkt_value_
		, CASE
			WHEN Iliquid_Indicator =1 THEN 1 -- In 1 day = 366
			WHEN Loan_Indicator = 1
			THEN (
				CASE Markit_Liquidity_Score
				WHEN 1 THEN COALESCE(ovr.Time_To_Liquidate, 5)
				WHEN 2 THEN COALESCE(ovr.Time_To_Liquidate, 15)
				WHEN 3 THEN COALESCE(ovr.Time_To_Liquidate, 20)
				WHEN 4 THEN COALESCE(ovr.Time_To_Liquidate, 30)
				WHEN 5 THEN COALESCE(ovr.Time_To_Liquidate, 90)
				END 
				)
			WHEN (Applicable_Daily_Volume_Country IS NOT NULL AND Applicable_Daily_Volume_Country > 0 AND Applicable_Daily_Volume_Country> ISNULL(Applicable_Daily_Volume,0) ) THEN CEILING(Quantity / Applicable_Daily_Volume_Country)
			WHEN (Applicable_Daily_Volume IS NOT NULL AND Applicable_Daily_Volume >0) THEN CEILING(Quantity / Applicable_Daily_Volume)
			WHEN Rating = 'NA' AND g.Currency_ID IS NOT NULL   THEN 3
			WHEN Rating = 'NA' AND g.Currency_ID IS NULL       THEN 5

			WHEN Rating = 'IG1' AND Market_Sector_Des = 'Govt' AND g.Currency_ID  IS NOT NULL THEN 1
			WHEN Rating = 'IG1' AND Market_Sector_Des = 'Govt' AND g.Currency_ID  IS NULL     THEN 3
			WHEN Rating = 'IG1' AND ( Market_Sector_Des != 'Govt'  OR Market_Sector_Des IS NULL) THEN 1

			WHEN Rating = 'IG2' AND DATEDIFF(day, h.Issue_Dt, h.Nav_Date)/365.25 < 1  THEN 1
			WHEN Rating = 'IG2' AND DATEDIFF(day, h.Issue_Dt, h.Nav_Date)/365.25 >= 1  THEN 3

			WHEN Rating IN ('HY1', 'HY2') AND DATEDIFF(day, h.Issue_Dt, h.Nav_Date)/365.25 < 0.25  THEN 1
			WHEN Rating IN ('HY1', 'HY2') AND DATEDIFF(day, h.Issue_Dt, h.Nav_Date)/365.25 < 1  THEN 3
			WHEN Rating IN ('HY1', 'HY2') THEN 5

			WHEN Rating IN ('D1', 'D2') THEN 90
			WHEN Rating = 'NR' THEN 5
			WHEN Asset_Type_ID = 3 THEN 5 -- Bond without rating
		END AS Time_to_Liquidate
		-- , CASE WHEN ee.Instrument_ID IS NOT NULL
		-- 	THEN (hmk.[Value] * Delta_Factor )* ee.Liquidation_Cost + (1-hmk.[Value] * Delta_Factor) * h.haircut
		-- ELSE haircut
		-- END As final_haircut
	INTO #main
	FROM #haircuts h
	LEFT JOIN @G10_Curr g on h.Instrument_Currency_ID = g.Currency_ID
	LEFT JOIN UTILITY.LIQUIDITY_SANCTIONED_ISINS rs ON rs.ISIN = h.Instrument_ISIN
	LEFT JOIN @Scenario_Loan_Param_Overwrites ovr ON ovr.Scenario_ID = h.Scenario_ID AND ovr.Liquidity_Rating = h.Markit_Liquidity_Score
	WHERE 1=1
        --and h.Instrument_ID = 689816
        --and h.Scenario_ID = 1

	IF OBJECT_ID('tempdb..#final') IS NOT NULL DROP TABLE #final
	SELECT 
		*
		, CASE 
			WHEN Iliquid_Indicator = 1 THEN Market_Value_Subfund_Ccy -- Full recovery
			WHEN (Applicable_Daily_Volume_Country IS NOT NULL AND Applicable_Daily_Volume_Country > 0 AND Applicable_Daily_Volume_Country> ISNULL(Applicable_Daily_Volume,0))
				THEN  IIF((Quantity - ((i.number-1)*Applicable_Daily_Volume_Country)) > Applicable_Daily_Volume_Country
					, (Recovered_Mkt_value_ / Quantity) * Applicable_Daily_Volume_Country
					, (Quantity - ((i.number-1) * Applicable_Daily_Volume_Country ))* Recovered_Mkt_value_ / Quantity)  
			WHEN (Applicable_Daily_Volume IS NOT NULL AND Applicable_Daily_Volume > 0 AND Quantity > 0)
				THEN  IIF((Quantity - ((i.number-1)*Applicable_Daily_Volume)) > Applicable_Daily_Volume
					, (Recovered_Mkt_value_ / Quantity) * Applicable_Daily_Volume
					, (Quantity - ((i.number-1) * Applicable_Daily_Volume ))* Recovered_Mkt_value_ / Quantity)  
			WHEN Applicable_Daily_Volume IS NOT NULL AND Quantity < 0
				THEN IIF(ABS(Quantity + (i.number-1) * (Applicable_Daily_Volume )) > Applicable_Daily_Volume
					, Recovered_Mkt_value_ / Quantity * Applicable_Daily_Volume
					, (Quantity + ((i.number -1) * Applicable_Daily_Volume)) * Recovered_Mkt_value_ / Quantity)
		ELSE m.Recovered_Mkt_value_ / ISNULL(m.Time_to_Liquidate,1)
        --WHEN (m.Time_to_Liquidate IS NOT NULL OR m.Time_to_Liquidate<>0)
        --THEN m.Recovered_Mkt_value_ / m.Time_to_Liquidate
		END AS Recovered_Mkt_value
		, ISNULL([Days_To_Settle], 2) + i.number - 1 AS [Day]
    INTO #final
	FROM #main m
	JOIN    master.dbo.spt_values AS i ON i.type = 'P' AND i.number BETWEEN 1 AND ISNULL(m.Time_to_Liquidate,1)
    WHERE 1=1
         --AND Scenario_ID =1
         --and Instrument_ID = 689816

	DELETE fi
	FROM BBG.LST_CASH_FLOWS fi
	WHERE 1=1
		AND EXISTS (SELECT * FROM TEMP.LIQUIDITY_EXPORT_STAGING m WHERE m.Subfund_ID = fi.Subfund_ID AND m.Nav_Date = fi.NAV_Date)
		AND fi.Liquidity_Asset_Class_ID = @Asset_Class_ID
		AND (fi.Subfund_ID = @SF_ID OR @SF_ID IS NULL)

	INSERT INTO BBG.LST_CASH_FLOWS (Scenario_ID, NAV_Date, Subfund_ID, Liquidity_Asset_Class_ID, [Day], Recovered_Market_Value)
	-- MERGE BBG.LST_CASH_FLOWS AS target USING (
    SELECT
		m.Scenario_ID
		, m.Nav_Date
		, m.Subfund_ID
		, @Asset_Class_ID -- hard coded asset class because we also have convertibles in this section (3)
		, m.[Day]
		, SUM(m.Recovered_Mkt_value) AS Recovered_Market_Value
	FROM #final m
	WHERE Time_to_Liquidate IS NOT NULL
	GROUP BY
		m.Scenario_ID
		, m.Nav_Date
		, m.Subfund_ID
		, m.[Day]
	
	DELETE fi
	FROM BBG.FIXED_INCOMES fi
	WHERE 1=1
		AND EXISTS (SELECT * FROM TEMP.LIQUIDITY_EXPORT_STAGING m WHERE m.Subfund_ID = fi.Subfund_ID AND m.Nav_Date = fi.NAV_Date)
		AND (fi.Subfund_ID = @SF_ID OR @SF_ID IS NULL)

	INSERT INTO BBG.FIXED_INCOMES (
		[NAV_Date]
		,[PTF_ID]
		,[Subfund_ID]
		,[Instrument_ID]
		,[Security_Name]
		,[BBG_Ticker]
		,[MKT_Value]
		,[Perc_TNA]
		,[Instrument_Type]
		,[Bid_Ask_Spread]
		,[Ownership]
		,[Duration]
		,[Maturity]
		,[Volatility]
		,[Rating]
		,[Callable]
		,[Liquidity_Score]
		,[Haircut]
		,[Days_To_Settle]
		,[MKT_Value_After_Haircut]
		,[Days_To_Liquidate]
	)
	SELECT
		m.Nav_Date AS Nav_Date
		, m.Subfund_CA_ID as PTF_ID
		, m.Subfund_ID
		, m.Instrument_ID
		, m.Instrument_Description AS Security_Name
		, m.Instrument_Bloomberg_Code AS BBG_Ticker
		, m.Market_Value_Subfund_Ccy AS MKT_Value
		, m.Market_Value_Subfund_Ccy / ast.total_assets as Perc_TNA
		, m.Market_Sector_Des AS Instrument_Type
		, m.Spread_Bid_Ask * 10000 AS Bid_Ask_Spread
		, m.Ownership AS [Ownership]
		, NULL AS Duration
		, m.Maturity_in_Year AS Maturity
		, m.Volatility_Mid_Bid_Ask AS Volatility
		, IIF(Loan_Indicator = 1, NULL ,m.Rating) AS Rating
		, m.Is_Callable AS Callable
		--
		-- , m.init_Score
		-- , m.Ownership_effect
		-- , m.Maturity_Effect
		-- , m.Duration_Effect
		-- , m.Call_Effect
		-- , m.Rating_Effect
		-- , m.Vol_Effect
		--
		, IIF(Loan_Indicator = 0 ,m.Liquidity_Score, m.Markit_Liquidity_Score) AS [Liquidity_Score]
		, m.final_haircut AS Haircut
		, m.Days_To_Settle
		, m.Recovered_Mkt_value_ AS MKT_Value_After_Haircut
		, m.Time_to_Liquidate AS Days_To_Liquidate
	FROM #main m
	LEFT JOIN dbo.VIEW_TOTAL_NET_ASSETS ast ON ast.subfund_id = m.subfund_id AND ast.NAV_NAVdate = m.Nav_Date
	WHERE 1=1
		AND Scenario_ID = 1
;

	insert into [UTILITY].[APP_LOGS] ([EntryID], [Type] , [EntryDate] ,[ApplicationName] )
	values (newid(), 'ProcedureEnd', getdate(), 'LIQUIDITY_FIXED_INCOMES_ST')


end try

begin catch

	insert into [UTILITY].[APP_LOGS] ([EntryID], [Type] , [EntryDate] ,[ApplicationName] ,[ExceptionMessage] ,[Message])
	values (newid(), 'Error', getdate(), ERROR_PROCEDURE(), ERROR_LINE() ,ERROR_MESSAGE())

end catch

END
GO


