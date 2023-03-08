import {Container, Row, Col, Form, Button, InputGroup } from "react-bootstrap";
import AuthContext from './AuthContext.js';
import { useContext } from 'react';

const onSubmit = (event) => {
    console.log("Hello World!!!!!!!!!")
    event.preventDefault();
}

const CreateFund = () => {
  const {loginUser} = useContext(AuthContext)  
  return (
    <Container fluid>
        <Row className="vh-100">
            <Col md={{ span: 6, offset: 3 }}>    
                <Form onSubmit={loginUser}>
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
                    <Form.Select aria-label="Default select example">
                        <option>Open this select menu</option>
                        <option value="1">One</option>
                        <option value="2">Two</option>
                        <option value="3">Three</option>
                    </Form.Select>
                    <Form.Label>Days to liquidate</Form.Label>
                    <Form.Select aria-label="Default select example">
                        <option>Open this select menu</option>
                        <option value="1">One</option>
                        <option value="2">Two</option>
                        <option value="3">Three</option>
                    </Form.Select>
                    <Form.Label>VaR Limit</Form.Label>
                    <InputGroup className="mb-3">
                        <Form.Control placeholder="VaR Limit" />
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