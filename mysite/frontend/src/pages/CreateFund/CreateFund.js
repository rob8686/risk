import {Container, Row, Col, Form, Button, InputGroup } from "react-bootstrap";
import { useNavigate } from 'react-router-dom';
import AuthContext from '../../services/AuthContext.js';
import { useContext } from 'react';
import { fundPostData } from "../../services/ApiService.js";


const CreateFund = () => {

  const {authTokens, logoutUser} = useContext(AuthContext)  
  const user_navigate = useNavigate();


    const handleSubmit = async(e) => {
    e.preventDefault();
    await fundPostData('api/fund/',user_navigate, {
        name: e.target.fundname.value, 
        currency: e.target.currency.value, 
        aum: e.target.aum.value, 
        benchmark:parseInt(e.target.benchmark.value), 
        liquidity_limit: e.target.liquidity.value
    })}

  return (
    <Container fluid>
        <Row className="vh-100">
            <Col md={{ span: 6, offset: 3 }}>    
                <Form onSubmit={handleSubmit} className='content'>
                    <h3>Create Position</h3>
                    <Form.Group className="mb-3" controlId="formBasicFundName" >
                        <Form.Label>Fund Name</Form.Label>
                        <Form.Control type="text" name="fundname" placeholder="Fund Name" />
                    </Form.Group>
                    <Form.Group className="mb-3" controlId="formBasicCurrency" >
                        <Form.Label>Currency</Form.Label>
                        <Form.Control type="text" name="currency" placeholder="Currency" maxLength="3"/>
                    </Form.Group>
                    <Form.Group className="mb-3" controlId="formBasicAum" >
                        <Form.Label>AUM</Form.Label>
                        <Form.Control type="number" name="aum" placeholder="AUM"/>
                    </Form.Group>
                    <Form.Label>Performance Benchmark</Form.Label>
                    <Form.Select aria-label="Default select example" name="benchmark">
                        <option value='1'>SPDR S&P 500 ETF Trust (SPY)</option>
                        <option value="2">Two</option>
                        <option value="3">Three</option>
                    </Form.Select>
                    <Form.Label>Days to liquidate</Form.Label>
                    <Form.Select aria-label="Default select example" name="liquidity">
                        <option value="1">1</option>
                        <option value="7">7</option>
                        <option value="30">30</option>
                        <option value="90">90</option>
                        <option value="180">180</option>
                        <option value="365">365</option>
                        <option value="365+">365+</option>
                    </Form.Select>
                    <Form.Label>VaR Limit</Form.Label>
                    <InputGroup className="mb-3">
                        <Form.Control placeholder="VaR Limit" name="var" />
                        <InputGroup.Text>%</InputGroup.Text>
                    </InputGroup>
                    <Button variant="primary" type="submit">
                        Submit
                    </Button>
                </Form>
            </Col>
        </Row>
  </Container>
  )
}

export default CreateFund