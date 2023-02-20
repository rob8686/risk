import { useState, useEffect, useContext } from 'react'
//import Table from './Table.js';
import AddFund from './AddFund.js';
import {BrowserRouter as Router, Switch, Route, Routes, Link, Redirect} from 'react-router-dom'
import Button from 'react-bootstrap/Button'
import Table from 'react-bootstrap/Table'
import RiskTable from './RiskTable.js';
import RiskButton from './RiskButton.js';
import React from 'react';
import AuthContext from './AuthContext.js'

const Funds = (props) => {
  const [data, setData] = useState([props.data])
  const {authTokens, logoutUser} = useContext(AuthContext)
  
  const refresh = async (fundId, fundCurrency,fundBenchmark,requestOptions = '') => {
    const response = await props.fetchData(`http://127.0.0.1:8000/risk/api/risk_data/${fundId}/${fundCurrency}/${fundBenchmark}`, requestOptions)
    props.getFunds()
  }  

  const handleClick = (event, fundId, fundCurrency,fund_benchmark) => {
    refresh(fundId, fundCurrency,fund_benchmark)
}

const getFunds = async() =>{
  let response = await fetch('http://127.0.0.1:8000/api/fund/', {
      method:'GET',
      headers:{
          'Content-Type':'application/json',
          'Authorization':'Bearer ' + String(authTokens.access)
      }
  })
  let data = await response.json()

  if(response.status === 200){
      setNotes(data)
  }else if(response.statusText === 'Unauthorized'){
      logoutUser()
  }
  
}


  const columns = [
    {Header: 'Id', accessor: 'id'},
    {Header: 'Name', accessor: 'name',
    Cell: ({ value }) => (
      <div style={{ wordBreak: 'break-word' }}>
        {value}
      </div>
    )
    },
    {Header: 'Currency', accessor: 'currency',},
    {Header: 'AUM', accessor: 'aum',},
    {Header: 'Date', accessor: 'last_date',},
    {Header: 'liquidity_limit', accessor: 'liquidity_limit',},
    {Header: 'Benchmark', accessor: 'benchmark',},
    {Header: 'Portfolio', accessor: row => 'Portfolio',
    Cell: ({ cell }) => (
      <Link to={`/positions/?fund=${cell.row.values.id}`}>
        <Button value='portfolio'>
          Portfolio
        </Button>
      </Link>
    )}, 
    {Header: 'Run Risk', accessor: row => 'Run',
    Cell: ({ cell }) => (
      <Button value='Run' onClick={(e) => handleClick(e,cell.row.values.id,cell.row.values.currency,cell.row.values.benchmark)}>
        Run
      </Button>
    )},
    {Header: 'Liquidity', accessor: 'liquidity_status',
    Cell: ({ cell }) => (
      <Link to={`/liquidity/${cell.row.values.id}`}>
        <RiskButton status={cell.row.values.liquidity_status}/>
      </Link>
    )},
    {Header: 'Performance', accessor: 'performance_status',
    Cell: ({ cell }) => (
      <Link to={`/performance/${cell.row.values.id}`}>
        <RiskButton status={cell.row.values.performance_status}/>
      </Link>
    )},
  ]

  if (!data.length) return <div>Loading...</div>

  return (
    <div>
        <input/>
        <AddFund getFunds={props.getFunds}/>
        <RiskTable style='responsive striped bordered hover' data={props.data} columns={columns}/>
    </div>
  )
}

export default Funds