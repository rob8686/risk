import { useState, useEffect, useContext } from 'react'
import {BrowserRouter as Router, Switch, Route, Routes, Link, Redirect,useLocation} from 'react-router-dom'
import Button from 'react-bootstrap/Button'
import Table from 'react-bootstrap/Table'
import RiskTable from './RiskTable.js';
import RiskButton from './RiskButton.js';
import React from 'react';
import AuthContext from './AuthContext.js'
import {fetchData2} from '../services/ApiService.js'

const Funds = (props) => {
  const [funds, setFunds] = useState([])
  const {authTokens, logoutUser} = useContext(AuthContext)
  const location = useLocation();
  

  useEffect(() => {
    getFunds()
  }, [location]) 

  const getFunds = async () => {
    const data = await fetchData2('api/fund/')
    setFunds(data)
  }

// remove benchmark 
const handleClick = async(e,fundId, fundCurrency,fund_benchmark) => {
  e.preventDefault();
  await fetchData2(`risk/api/risk_data/${fundId}/${fundCurrency}/${fund_benchmark}`)
  getFunds()
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
    {Header: 'Portfolio', accessor: row => 'Portfolio',
    Cell: ({ cell }) => (
      <Link to={`/positions/${cell.row.values.id}`}>
        <Button value='portfolio'>
          Portfolio
        </Button>
      </Link>
    )}, 
    {Header: 'Run Risk', accessor: row => 'Run',
    Cell: ({ cell }) => (
      <Button value='Run' onClick={(e) => handleClick(e,cell.row.values.id,cell.row.values.currency,cell.row.values.last_date)}>
        Run
      </Button>
    )},
    {Header: 'Liquidity', accessor: 'liquidity_status',
    Cell: ({ cell }) => (
      <Link to={`/liquidity/${cell.row.values.id}/${cell.row.values.last_date}`}>
        <RiskButton status={cell.row.values.liquidity_status}/>
      </Link>
    )},
    {Header: 'Performance', accessor: 'performance_status',
    Cell: ({ cell }) => (
      <Link to={`/performance/${cell.row.values.id}/${cell.row.values.last_date}`}>
        <RiskButton status={cell.row.values.performance_status}/>
      </Link>
    )},
    {Header: 'Market Risk', accessor: 'market_risk',
    Cell: ({ cell }) => (
      <Link to={`/market_risk/${cell.row.values.id}/${cell.row.values.last_date}`}>
        <RiskButton status={cell.row.values.performance_status}/>
      </Link>
    )},
  ]

  return (
    <div className='content'>
        <RiskTable style='table responsive hover' data={funds} columns={columns}/>

    </div>
  )
}

export default Funds