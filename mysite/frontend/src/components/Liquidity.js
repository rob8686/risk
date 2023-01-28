import { useState, useEffect } from 'react'
import React from 'react'
import ExtandableRiskTable from './ExtandableRiskTable.js';
import RiskLineChart from './RiskLineChart.js';
import { AiOutlineArrowRight, AiOutlineArrowDown } from 'react-icons/ai'
import { Line } from 'recharts';

function Liquidity2() {
    let url = new URL(window.location.href)
    const [data, setData] = useState([])
    const [fundNum, setFundNum] = useState([url.searchParams.get("fund")])

    let rowList=[];
    let headerList=[<th>Ticker</th>,,<th>1</th>,<th>7</th>,<th>30</th>,<th>90</th>,<th>180</th>,<th>365</th>,<th>365+</th>];

    useEffect(() => {
        getData()
      }, [])

    const getData = async () => {
        const riskData = await fetchData(`http://127.0.0.1:8000/risk/api/liquidity/${fundNum}`)    //+fundNum)
        setData(riskData)
        console.log('RISK DATA')
        console.log(riskData)
        console.log(riskData['result'])
      }  
      
      const fetchData = async (url, requestOptions = '') => {
        const response = (requestOptions === '') ?  await fetch(url) : await fetch(url,requestOptions);
        const data = await response.json();
        return data; 
      }

      console.log('DATAAAAAAAAAAAAAAAAAA')
      console.log(data)
      console.log(data.length)

    const columns = [
        {
          // Build our expander column
          id: 'expander', // Make sure it has an ID
          Header: ({ getToggleAllRowsExpandedProps, isAllRowsExpanded }) => (
            <span {...getToggleAllRowsExpandedProps()}>
              {isAllRowsExpanded ? <AiOutlineArrowDown/> : <AiOutlineArrowRight/>}
            </span>
          ),
          Cell: ({ row }) =>
            // Use the row.canExpand and row.getToggleRowExpandedProps prop getter
            // to build the toggle for expanding a row
            row.canExpand ? (
              <span
                {...row.getToggleRowExpandedProps({
                  style: {
                    // We can even use the row.depth property
                    // and paddingLeft to indicate the depth
                    // of the row
                    paddingLeft: `${row.depth * 2}rem`,
                  },
                })}
              >
                {row.isExpanded ? <AiOutlineArrowDown/> : <AiOutlineArrowRight/>}
              </span>
            ) : null,
        },
            {
              Header: 'Liq %',
              accessor: 'type',
            },
            {
              Header: '1',
              accessor: '1',
            },
            {
              Header: '7',
              accessor: '7',
            },
            {
              Header: '30',
              accessor: '30',
            },
            {
              Header: '90',
              accessor: '90',
            },
            {
              Header: '180',
              accessor: '180',
            },
            {
              Header: '365',
              accessor: '365',
            },
            {
              Header: '365+',
              accessor: '365+',
            },
      ]


    if (!data['result']) return <div>Loading...</div>  
    const lines= [
        <Line type="monotone" dataKey="100" stroke="#8884d8" activeDot={{ r: 8 }} />,
        <Line type="monotone" dataKey="50" stroke="#82ca9d" />
    ]

    console.log('LINESSSSSSSSSSSSSS')
    console.log(lines)

    return (
      <div>
          <RiskLineChart data={data['cumulative']} lines={lines} dataKey={'name'}/>
          <ExtandableRiskTable style='striped bordered hover' data={data['result']} columns={columns}/>
      </div>
    )
    
}

export default Liquidity2