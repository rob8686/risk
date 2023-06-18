import { useState, useEffect } from 'react';
import Tab from 'react-bootstrap/Tab';
import Tabs from 'react-bootstrap/Tabs';
import Table from 'react-bootstrap/Table'

const MarketRisk = () => {

  const fundNum = window.location.href.split("/").pop()
  const [data, setData] = useState([])

  useEffect(() => {
    getData()
  }, [])
  
  let getData = async ()=> {

    let response = await fetch(`http://127.0.0.1:8000/risk/api/market_risk/${fundNum}`, {
        method:'GET',
        headers:{
            'Content-Type':'application/json'
        },
        //body:JSON.stringify({'refresh':authTokens?.refresh})
    })

    let data = await response.json()
    
    if (response.status === 200){
      setData(data)
    }else{
        console.log('ERROR LOADING DATA')
        // Update here?
    }
  }

  console.log('DATAAAAAAAAAAAAAA')
  console.log(data)
  if (!Object.keys(data).length) return <div>Loading...</div>
  return (
    <Tabs
      defaultActiveKey="hist"
      transition={false}
      id="noanim-tab-example"
      className="mb-3 content"
    >
      <Tab eventKey="hist" title="VaR - Historical Simulation">
        <div className='content'>
        <div><b>1 Day VaR - 99% CI:</b>{data['factor_var']['var_1d'].at(-1)}</div>
        </div>  
      </Tab>
      <Tab eventKey="profile" title="VaR - Parametric">
        <div className='content'>
        <div><b>1 Day VaR - 99% CI:</b>{data['parametric_var']['var_1_day']}</div>  
          <Table>
            <thead>
              <tr>
                <th key={0}></th>  
                {data['tickers'].map((ticker,index)=>{
                  return <th key={index + 1}>{ticker}</th>
                })}
              </tr>
            </thead>
            <tbody>
              {data['parametric_var']['correlation'].map((row,index)=>{
                return(
                <tr key={index}>
                  <th>{data['tickers'][index]}</th>
                  {row.map((value,index)=>{
                    return <td key={index}>{value}</td>
                  })}
                </tr>
                )})}
            </tbody>
          </Table>
        </div>
      </Tab>
      <Tab eventKey="stress" title="Stress Tests">
        Tab content for Contact
      </Tab>
    </Tabs>
  );
}

export default MarketRisk