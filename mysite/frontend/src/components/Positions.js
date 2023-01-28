import { useState, useEffect } from 'react'
import AddPosition from './AddPosition';
import TableInput from './TableInput';
import Table from 'react-bootstrap/Table'
import Button from 'react-bootstrap/Button'
import RiskTable from './RiskTable.js';

const Positions = (props) => {
    let url = new URL(window.location.href)
    const [positions, setPositions] = useState([])
    const [fundNum, setFundNum] = useState([url.searchParams.get("fund")])
    const rowList=[];

    useEffect(() => {
        getPositions(fundNum)
    }, [])

    console.log('posiitons',positions)
    const getPositions = async (fundNum) => {
        const PositionsFromServer = await fetchData('http://127.0.0.1:8000/api/position/?fund='+fundNum)
        PositionsFromServer.forEach((elem) =>{
            let securities = elem['securities'];
            delete securities.id;
            delete elem.securities;
            elem = Object.assign(elem, securities,{'Delete':'Delete'});
        })
        setPositions(PositionsFromServer)
    }
      
    const fetchData = async (url, requestOptions = '') => {
        const response = (requestOptions === '') ?  await fetch(url) : await fetch(url,requestOptions);
        if (requestOptions['method'] != "DELETE"){
            const data = await response.json();
            return data;  
        }
    }

    const deletePosition = async (postionId) => {
        const deleteRequestOptions ={
            method:"DELETE",
            headers:{"Content-Type":"application/json"},
            body: {}
        }
        const FundsFromServer = await fetchData(`http://127.0.0.1:8000/api/position/${postionId}/`, deleteRequestOptions)
        getPositions(fundNum)
      }  
    
    const handleClick = (event,positionId) => {
        deletePosition(positionId)
    }

    const headerList=[<th>ID</th>,<th>Name</th>,<th>Ticker</th>,<th>Ccy</th>,
        <th>Sector</th>,<th>Industry</th>,<th>Date</th>,<th>Last price</th>,
        <th>Quantity</th>,<th>Market Value Local</th>, <th>FX Rate</th>,
        <th>Market Value Base</th>, <th>Percent AUM</th>,<th>Delete</th>];


    positions.forEach((obj,index)=>{
        rowList.push(
        <tr key={index}>
          <td>{obj.id}</td>
          <td>{obj.name}</td>
          <td>{obj.ticker}</td>
          <td>{obj.currency}</td>
          <td>{obj.sector}</td>
          <td>{obj.industry}</td>
          <td>{obj.price_date}</td>
          <td>{obj.last_price}</td>
          <td><TableInput value={obj.quantity} getPositions={getPositions} fetchData={fetchData} positionNum={obj.id}/></td>
          <td>{obj.mkt_value_local}</td>
          <td>{obj.fx_rate}</td>
          <td>{obj.mkt_value_base}</td>
          <td>{obj.percent_aum}</td>
          <td><button onClick={(e)=> handleClick(e,obj.id)}>{obj.id}</button></td>
        </tr>)
      })

    const columns = [
      {Header: 'Id', accessor: 'id'},
      {Header: 'Name', accessor: 'name',},
      {Header: 'Ticker', accessor: 'ticker',},
      {Header: 'Currency', accessor: 'currency',},
      {Header: 'Sector', accessor: 'sector',},
      {Header: 'Industry', accessor: 'industry',},
      {Header: 'Price Date', accessor: 'price_date',},
      {Header: 'Last Price', accessor: 'last_price',},
      {Header: 'Quantity', accessor: 'quantity',},
      {Header: 'Mkt Value Local', accessor: 'mkt_value_local',},
      {Header: 'FX Rate', accessor: 'fx_rate',},
      {Header: 'Mkt Value Base', accessor: 'mkt_value_base',},
      {Header: 'Percent AUM', accessor: 'percent_aum',},
      {Header: 'Delete',
      Cell: ({ cell }) => (
        <Button value={cell.row.values.id} onClick={(e) => handleClick(e,cell.row.values.id)}>
          {cell.row.values.id}
        </Button>
      )
      },
    ]


  if (!positions.length) return <div>Loading...</div>  

  return (
    <div>
        <AddPosition getPositions={getPositions} fundNum ={fundNum}/>
        <Table striped bordered hover size="sm">
          <tr>
            {headerList}
          </tr>
          <tbody>
            {rowList}  
          </tbody>
        </Table>
        <RiskTable style='striped bordered hover' data={positions} columns={columns}/>
    </div>
  )
}

export default Positions
