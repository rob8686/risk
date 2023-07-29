import { useState, useEffect, useRef } from 'react';
import Tab from 'react-bootstrap/Tab';
import Tabs from 'react-bootstrap/Tabs';
import Table from 'react-bootstrap/Table'
import MarketRiskBarChart from './MarketRiskBarChart';
import RiskTable from './RiskTable.js';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import SideTable from './SideTable.js';
import MarketRiskAreaChart from './MarketRiskAreaChart';
import MarketRiskVerticalBarChart from './MarketRiskVerticalBarChart';
import './MarketRisk.css';


const MarketRisk = () => {

  const fundNum = window.location.href.split("/").pop()
  const [data, setData] = useState([])
  const [height, setHeight] = useState()
  const ref = useRef(null)

  useEffect(() => {
    getData()
  }, [])

  useEffect(() => {
    //setHeight(ref.current.clientHeight)
  })

  //https://stackoverflow.com/questions/73247936/how-to-dynamically-track-width-height-of-div-in-react-js  
  useEffect(() => {
    if (!ref.current) {
      // we do not initialize the observer unless the ref has
      // been assigned
      return;
    }

    // we also instantiate the resizeObserver and we pass
    // the event handler to the constructor
    const resizeObserver = new ResizeObserver(() => {
      if(ref.current.offsetHeight !== height) {
        console.log('SET HEIGHT!!!!!!!!!!!!!!!!!!!!!!!!!')
        setHeight(ref.current.offsetHeight);
      }
    });
    
    // the code in useEffect will be executed when the component
    // has mounted, so we are certain observedDiv.current will contain
    // the div we want to observe
    resizeObserver.observe(ref.current);


    // if useEffect returns a function, it is called right before the
    // component unmounts, so it is the right place to stop observing
    // the div
    return function cleanup() {
      resizeObserver.disconnect();
    }
  },
  // only update the effect if the ref element changed
  [ref.current])
  
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

  const columns = [
    {Header: 'Date', accessor: 'name'},
    {Header: 'PL', accessor: 'PL', sortType: 'basic',
    Cell: ({ value }) => (value * 100).toFixed(2) + '%'}
  ]

  {data['tickers'].map((ticker,index)=>{
    //return <th key={index + 1}>{ticker}</th>
    console.log('NEW HELLO')
    console.log(index, ticker)
  })}

  console.log(data['factor_var']['chart_list'])
  return (
    <Tabs
      defaultActiveKey="hist"
      transition={false}
      id="noanim-tab-example"
      className="mb-3 content"
    >
      <Tab eventKey="hist" title="VaR - Historical Simulation">
        <Container fluid>
        <Row>
          <Col className='content'>
            <b>1 Day VaR - 99% CI:</b>{data['factor_var']['var_1d'].at(-1)}
          </Col>
        </Row>
        <Row>
          <Col xs={9}>
              <div>
                <MarketRiskBarChart data={data['factor_var']['chart_list']} axis={'name'} bar={'PL'}></MarketRiskBarChart>
              </div>
          </Col>
          <Col>
            <div>  
              <SideTable data={data['factor_var']['chart_list']} columns={columns}/> 
            </div>
          </Col>
          <Col>
            <div ref={ref}>
              HEIGHTTTTTTTTTTTTTTT  
              {height}
            </div>
          </Col>
        </Row>
        </Container>  
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
                    console.log('VALUE!!!!!!!!!!!!!!!!!!')
                    console.log(value)
                    console.log(value.value)
                    return <td key={index} className={Number(value) > 0 ? 'text-success' : 'text-danger'}>{value}</td>
                  })}
                </tr>
                )})}
            </tbody>
          </Table>
          <MarketRiskAreaChart data={data['hist_series']}/>
        </div>
      </Tab>
      <Tab eventKey="stress" title="Stress Tests">
        <div>
          <MarketRiskVerticalBarChart data={data['stress_tests']['stress_tests']} axis={'stress'} bar={'result'}></MarketRiskVerticalBarChart>
        </div>
      </Tab>
    </Tabs>
  );
}

export default MarketRisk