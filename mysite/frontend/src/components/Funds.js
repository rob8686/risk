import { useState, useEffect, useContext } from 'react'
//import Table from './Table.js';
import AddFund from './AddFund.js';
import {BrowserRouter as Router, Switch, Route, Routes, Link, Redirect,useLocation} from 'react-router-dom'
import Button from 'react-bootstrap/Button'
import Table from 'react-bootstrap/Table'
import RiskTable from './RiskTable.js';
import RiskButton from './RiskButton.js';
import React from 'react';
import AuthContext from './AuthContext.js'

const Funds = (props) => {
  //const [data, setData] = useState([props.data])
  const [funds, setFunds] = useState([])
  const {authTokens, logoutUser} = useContext(AuthContext)
  const location = useLocation();

  useEffect(() => {
    getFunds()
  }, [location]) 

  const refresh = async (fundId, fundCurrency,fundBenchmark,requestOptions = '') => {
    //const response = await props.fetchData(`http://127.0.0.1:8000/risk/api/risk_data/${fundId}/${fundCurrency}/${fundBenchmark}`, requestOptions)
    const response = await fetchData(`http://127.0.0.1:8000/risk/api/risk_data/${fundId}/${fundCurrency}`, requestOptions)
    getFunds()
  }  

  const handleClick = (event, fundId, fundCurrency) => {
    refresh(fundId, fundCurrency)
  }

const getFunds = async () => {
  const FundsFromServer = await fetchData('http://127.0.0.1:8000/api/fund/')
  setFunds(FundsFromServer)
}

const fetchData = async (url, requestOptions = '') => {
  const response = (requestOptions === '') ?  await fetch(url) : await fetch(url,requestOptions);
  const data = await response.json();
  return data; 
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
    {Header: 'Currency', accessor: 'currency',
    Cell: ({ value }) => <div style={{ textAlign: 'center' }}>{value}</div>,
    },
    {Header: 'AUM', accessor: 'aum',
    Cell: ({ value }) =>
    typeof value === 'number' ? <div style={{ textAlign: 'center' }}>{value.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}</div> : value,
    },
    {Header: 'Date', accessor: 'last_date',},
    //{Header: 'liquidity_limit', accessor: 'liquidity_limit',},
    //{Header: 'Benchmark', accessor: 'benchmark',},
    {Header: 'Portfolio', accessor: row => 'Portfolio',
    Cell: ({ cell }) => (
      //<Link to={`/positions/?fund=${cell.row.values.id}`}>
      <Link to={`/positions/${cell.row.values.id}`}>
        <Button value='portfolio'>
          Portfolio
        </Button>
      </Link>
    )}, 
    {Header: 'Run Risk', accessor: row => 'Run',
    Cell: ({ cell }) => (
      <Button value='Run' onClick={(e) => handleClick(e,cell.row.values.id,cell.row.values.currency)}>
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


  //if (!funds.length) return <div>Loading...</div>
  // <div style={{backgroundColor:'white', margin:'10px', padding:'10px', border: '5px solid blue',}}>
  // <RiskTable style='responsive striped bordered hover' data={funds} columns={columns}/>

  return (
    <div className='content'>
        <RiskTable style='table responsive hover' data={funds} columns={columns}/>

    </div>
  )
}

export default Funds