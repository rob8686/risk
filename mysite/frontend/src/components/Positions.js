import {BrowserRouter as Router, Switch, Route, Routes, Link, Redirect, useLocation} from 'react-router-dom'
import { useState, useEffect } from 'react'
import Button from 'react-bootstrap/Button'
import RiskTable from './RiskTable.js';
import CreatePosition from './CreatePosition.js';
import {fetchData2, deleteData2} from '../services/ApiService.js'

const Positions = (props) => {
    const location = useLocation(); 
    const [positions, setPositions] = useState([])
    const [fundNum, setFundNum] = useState([location.pathname.split('/').pop()])
    const rowList=[];

    useEffect(() => {
        getPositions(fundNum)
    }, [])


    console.log('posiitons',positions)
    const getPositions = async (fundNum) => {
        console.log('NEW GET POSITIONSSSSSSSSSSSSSSSSSS') 
        const data = await fetchData2('api/position/?fund=' + fundNum)//+fundNum)
        data.forEach((elem) =>{
            let securities = elem['securities'];
            delete securities.id;
            delete elem.securities;
            elem = Object.assign(elem, securities,{'Delete':'Delete'});
        })
        setPositions(data)
    }


    const handleClick = async (event,positionId) => {
      await deleteData2(`api/position/${positionId}/`)
      getPositions(fundNum)
    }

    const columns = [
      {Header: 'Id', accessor: 'id'},
      {Header: 'Name', accessor: 'name',},
      {Header: 'Ticker', accessor: 'ticker',},
      {Header: 'Currency', accessor: 'currency',},
      {Header: 'Sector', accessor: 'sector',},
      {Header: 'Industry', accessor: 'industry',},
      {Header: 'Price Date', accessor: 'price_date',},
      {Header: 'Last Price', accessor: 'last_price',
      Cell: ({ value }) =>
      typeof value === 'number' ? value.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',') : value,
      },
      {Header: 'Quantity', accessor: 'quantity',
      Cell: ({ value }) =>
      typeof value === 'number' ? value.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',') : value,
      },
      {Header: 'Mkt Value Local', accessor: 'mkt_value_local',
      Cell: ({ value }) =>
      typeof value === 'number' ? value.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',') : value,
      },
      {Header: 'FX Rate', accessor: 'fx_rate',},
      {Header: 'Mkt Value Base', accessor: 'mkt_value_base',
      Cell: ({ value }) =>
      typeof value === 'number' ? value.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',') : value,
      },
      {Header: 'Percent AUM', accessor: 'percent_aum',
      Cell: ({ value }) => (value * 100).toFixed(2) + '%',
      },
      {Header: 'Delete',
      Cell: ({ cell }) => (
        <Button value={cell.row.values.id} onClick={(e) => handleClick(e,cell.row.values.id)}>
          {cell.row.values.id}
        </Button>
      )
      },
    ]

 
  return (
    <div>
        <CreatePosition getPositions={getPositions}/>
        <div className='content'>
          <RiskTable style='responsive striped bordered hover table-condensed' data={positions} columns={columns}/>
        </div>
    </div>
  )
}

export default Positions
