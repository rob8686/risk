import { useState, useEffect } from 'react'
import React from 'react'
import ExtandableRiskTable from './ExtandableRiskTable.js';
import RiskLineChart from './RiskLineChart.js';
import { AiOutlineArrowRight, AiOutlineArrowDown } from 'react-icons/ai'
import { Line } from 'recharts';
import {Container, Row, Col, Card, Form, Button } from "react-bootstrap";


function Liquidity() {
    const date = window.location.href.split("/").slice(-2)[1]
    const fundNum = window.location.href.split("/").slice(-2)[0]
    console.log('FUnd Num')
    console.log(fundNum)
    console.log(date)
    const [data, setData] = useState([])

    useEffect(() => {
        getData()
      }, [])

    const getData = async () => {
        const riskData = await fetchData(`http://127.0.0.1:8000/risk/api/liquidity_data/${fundNum}/${date}`)
        setData(riskData['Liquidity_stats'])
      }  
      
      const fetchData = async (url, requestOptions = '') => {
        const response = (requestOptions === '') ?  await fetch(url) : await fetch(url,requestOptions);
        const data = await response.json();
        return data; 
      }

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
              accessor: 'day_1',
            },
            {
              Header: '7',
              accessor: 'day_7',
            },
            {
              Header: '30',
              accessor: 'day_30',
            },
            {
              Header: '90',
              accessor: 'day_90',
            },
            {
              Header: '180',
              accessor: 'day_180',
            },
            {
              Header: '365',
              accessor: 'day_365',
            },
            {
              Header: '365+',
              accessor: 'day_366',
            },
      ]


    if (!data['result']) return <div>Loading...</div>  
    const lines= [
        <Line type="monotone" dataKey="100" stroke="#8884d8" activeDot={{ r: 8 }} />,
        <Line type="monotone" dataKey="50" stroke="#82ca9d" />,
        <Line type="monotone" dataKey="30" stroke="#ffc658" />
    ]
    console.log('DATA NEW')
    console.log('NEW V" DATAAAAAAAAAAAAAAAAA')
    console.log(data)
    return (
      <Container>
        <Row>
          <Col>
            <div className='content'>
              <RiskLineChart data={data['cumulative']} lines={lines} dataKey={'name'}/>
            </div>
          </Col>
        </Row>
        <Row>
          <Col>
            <div className='content'>
              <ExtandableRiskTable style='striped bordered hover' data={data['result']} columns={columns}/>
            </div>
          </Col>
        </Row>
      </Container>
    )
    
}

export default Liquidity