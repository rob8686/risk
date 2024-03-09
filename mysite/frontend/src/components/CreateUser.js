import {Container, Row, Col, Form, Button } from "react-bootstrap";
import { useNavigate } from 'react-router-dom';
import {userPostData} from '../services/ApiService.js'
 

const CreateUser = () => {

    const navigate = useNavigate();

    const handleSubmit = async(e) => {
        e.preventDefault();
        if (e.target.password.value === e.target.repeat_password.value){
            await userPostData('login/create/', navigate, {username: e.target.username.value, password: e.target.password.value})
        }
        else{
            alert('Passwords do not match');
        }
    }
    
    return (
    <Container fluid>
        <Row className="vh-100">
            <Col md={{ span: 6, offset: 3 }}>    
                <Form className="content" onSubmit={handleSubmit}>
                    <h3>Create Account</h3>
                    <Form.Group className="mb-3" controlId="formBasicUserName" >
                        <Form.Label>Username</Form.Label>
                        <Form.Control type="text" name="username" placeholder="Username" />
                    </Form.Group>
                    <Form.Group className="mb-3" controlId="formBasicPassword">
                        <Form.Label>Password</Form.Label>
                        <Form.Control type="password" name="password" placeholder="Password" />
                    </Form.Group>
                    <Form.Group className="mb-3" controlId="formBasicConfirmPassword">
                        <Form.Label>Confirm Password</Form.Label>
                        <Form.Control type="password" name="repeat_password" placeholder="Confirm Password" />
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

export default CreateUser