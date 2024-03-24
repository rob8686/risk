import { useState, useEffect } from 'react';
import PivotBarChart from './PivotBarChart.js';
import { Bar, Line } from 'recharts';
import RiskLineChart from '../../components/RiskLineChart.js';
import Table from 'react-bootstrap/Table';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import {fetchData2} from '../../services/ApiService.js'

const Performance = () => {
    const [data, setData] = useState([])
    const date = window.location.href.split("/").slice(-2)[1]
    const fundNum = window.location.href.split("/").slice(-2)[0]

    useEffect(() => {
        getData()
      }, [])

      const getData = async () => {
        const data = await fetchData2(`risk/api/performance_data/${fundNum}/${date}`)
        setData(data)
      }
      
    if (!data['performance_pivots']) return <div>Loading...</div>  

    const keys = Object.keys(data['performance_history']["0"])
    const bar = [<Bar dataKey="perc_contrib" fill="#8884d8" barSize={20} rowHeight={30}/>]   
    const headerList=[<th></th>,<th>Fund</th>,<th>Benchmark</th>];
    const performance = data['performance_stats']
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
          <Col className='content'>
            <RiskLineChart data={data['performance_history']} lines={lines} dataKey={'date'}/>
          </Col>
          <Col className='content'>
            <Table responsive size="sm">
              <tr>
                {headerList}
              </tr>
              <tbody>
                {rowList}
              </tbody>
            </Table>
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
        <Row>
          <Col className='content'>
            <h4>Return Contribution by Currency</h4>
            <PivotBarChart data={data['performance_pivots']['currency']} dataKey={"label"} bar={bar}/>
          </Col>
          <Col className='content'>
            <h4>Return Contribution by Sector</h4>
            <PivotBarChart data={data['performance_pivots']['sector']} dataKey={"label"} bar={bar}/>
          </Col>
        </Row>
          <Row>
            <Col className='content'>  
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