import { useState, useEffect } from 'react'
//import Table from './Table.js';
import AddFund from './AddFund.js';
import {BrowserRouter as Router, Switch, Route, Routes, Link, Redirect} from 'react-router-dom'
import Button from 'react-bootstrap/Button'
import Table from 'react-bootstrap/Table'
import RiskTable from './RiskTable.js';
import React from 'react';

const Funds = (props) => {
  const [data, setData] = useState([props.data])
  
  const rowList=[];
  const headerList=[<th>ID</th>,<th>Fund Name</th>,<th>Currency</th>,<th>AUM</th>,<th>Date</th>,<th>Portfolio</th>];
  
  const refresh = async (fundId, fundCurrency,fundBenchmark,requestOptions = '') => {
    const response = await props.fetchData(`http://127.0.0.1:8000/risk/api/risk_data/${fundId}/${fundCurrency}/${fundBenchmark}`, requestOptions)
    props.getFunds()
  }  

  const handleClick = (event, fundId, fundCurrency,fund_benchmark) => {
    console.log('BENCHMARK?????')
    console.log(fund_benchmark)
    refresh(fundId, fundCurrency,fund_benchmark)
}

  props.data.forEach((obj,index)=>{
    rowList.push(
    <tr key={index}>
      <td>{obj.id}</td>
      <td>{obj.name}</td>
      <td>{obj.currency}</td>
      <td>{obj.aum}</td>
      <td>{obj.last_date}</td>
      <td><Link to={`/positions/?fund=${obj.id}`}>Position</Link></td>
      <td><Button type="button" className="btn btn-primarys" onClick={(e)=> handleClick(e,obj.id,obj.currency)}>Run</Button></td>
      <td><Link to={`/liquidity/?fund=${obj.id}`}>Liquidity</Link></td>
      <td><Link to={`/performance/?fund=${obj.id}`}>Performance</Link></td>
    </tr>)
  })

  const columns = [
    {Header: 'Id', accessor: 'id'},
    {Header: 'Name', accessor: 'name',},
    {Header: 'Currency', accessor: 'currency',},
    {Header: 'AUM', accessor: 'aum',},
    {Header: 'Date', accessor: 'last_date',},
    {Header: 'liquidity_limit', accessor: 'liquidity_limit',},
    {Header: 'Benchmark', accessor: 'benchmark',},
    {Header: 'Portfolio',

    Cell: ({ cell }) => (
      <Link to={`/positions/?fund=${cell.row.values.id}`}>
        <Button value='portfolio'>
          Portfolio
        </Button>
      </Link>
    )}, 
    {Header: 'Run Risk', 
    Cell: ({ cell }) => (
      <Button value='Run' onClick={(e) => handleClick(e,cell.row.values.id,cell.row.values.currency,cell.row.values.benchmark)}>
        Run
      </Button>
    )},
    {Header: 'Liquidity', 
    Cell: ({ cell }) => (
      <Link to={`/liquidity/?fund=${cell.row.values.id}`}>
        <Button value='Liquidity'>
          Liquidity
        </Button>
      </Link>
    )},
    {Header: 'Performance', 
    Cell: ({ cell }) => (
      <Link to={`/performance/?fund=${cell.row.values.id}`}>  
        <Button value='performance'>
          Performance
        </Button>
      </Link>
    )},
  ]

  if (!data.length) return <div>Loading...</div>

  return (
    <div>
        <AddFund getFunds={props.getFunds}/>
        <RiskTable style='responsive striped bordered hover' data={props.data} columns={columns}/>
        <Table striped bordered hover>
          <tr>
            {headerList}
          </tr>
          <tbody>
            {rowList}  
          </tbody>
        </Table>
    </div>
  )
}

export default Funds