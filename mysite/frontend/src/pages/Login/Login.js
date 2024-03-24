import {Container, Row, Col, Form, Button } from "react-bootstrap";
import AuthContext from '../../services/AuthContext.js';
import { useContext } from 'react';

const Login = () => {
  const {loginUser} = useContext(AuthContext)  
  return (
    <Container fluid>
        <Row className="vh-100">
            <Col md={{ span: 6, offset: 3 }}>    
                <Form className="content" onSubmit={loginUser}>
                    <h3>Login</h3>
                    <Form.Group className="mb-3" controlId="formBasicUserName" >
                        <Form.Label>Username</Form.Label>
                        <Form.Control type="text" name="username" placeholder="Username" />
                    </Form.Group>
                    <Form.Group className="mb-3" controlId="formBasicPassword">
                        <Form.Label>Password</Form.Label>
                        <Form.Control type="password" name="password" placeholder="Password" />
                    </Form.Group>
                    <Button variant="primary" type="submit">
                        Submit
                    </Button>
                </Form>
            </Col>
        </Row>
  </Container>
  )
}

export default Login