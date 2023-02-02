import { useState, useEffect } from 'react';
import PivotBarChart from './PivotBarChart';
import { Bar, Line } from 'recharts';
import RiskLineChart from './RiskLineChart.js';
import RiskLineChart2 from './RiskLineChart2.js';
import Table from 'react-bootstrap/Table';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';

const Performance = () => {
    const fundNum = window.location.href.split("/").pop()
    const [data, setData] = useState([])

    useEffect(() => {
        getData()
      }, [])

    const getData = async () => {
        const riskData = await fetchData(`http://127.0.0.1:8000/risk/api/performance/${fundNum}`)    //+fundNum)
        setData(riskData)
      }  
      
    const fetchData = async (url, requestOptions = '') => {
      const response = (requestOptions === '') ?  await fetch(url) : await fetch(url,requestOptions);
      const data = await response.json();
      return data; 
    }


    if (!data['performance']) return <div>Loading...</div>  

    const newData = data

    const keys = Object.keys(data['performance']['fund_history']["0"])
    const bar = [<Bar dataKey="perc_contrib" fill="#8884d8" />]   
    const headerList=[<th></th>,<th>Fund</th>,<th>Benchmark</th>];
    const performance = data['performance']['pivots']['performance']
    const itemArray = [['return','Return'], ['std','Volatility'],['sharpe','Sharpe Ratio']]
    
    const lines= [
      <Line type="monotone" dataKey="fund_history" stroke="#8884d8" dot={false} />,
      <Line type="monotone" dataKey="benchamrk_history" stroke="#82ca9d" dot={false}/>
  ]

  const rowList = itemArray.map((item)=>{
    return(
    <tr>
      <td><b>{item[1]}</b></td>
      <td>{performance['fund'][item[0]]}</td>
      <td>{performance['benchmark'][item[0]]}</td>
    </tr>
    )
  })
      
    return(
      <Container fluid>
        <Row>
          <Col md={12} lg={8}>
            <RiskLineChart data={data['performance']['fund_history']} lines={lines} dataKey={'Date'}/>
          </Col>
          <Col md={12} lg={4}>
            <Table responsive size="sm">
              <tr>
                {headerList}
              </tr>
              <tbody>
                {rowList}
              </tbody>
            </Table>
          </Col>
        </Row>
        <Row>
          <Col>
          <PivotBarChart data={data['performance']['pivots']['pivots']['currency']} dataKey={"currency"} bar={bar}/>
          </Col>
          <Col>
          <PivotBarChart data={data['performance']['pivots']['pivots']['sector']} dataKey={"sector"} bar={bar}/>
          </Col>
        </Row>
          <Row>
            <Col>  
              <Table striped bordered hover>
                <tr>
                  {headerList}
                </tr>
                <tbody>
                  {rowList}
                </tbody>
              </Table>
              </Col>
          </Row>
        </Container>
      )

}

export default Performance