import {Container, Row, Col, Form, Button } from "react-bootstrap";
import { useNavigate } from 'react-router-dom';
 

const CreateUser = () => {

    const navigate = useNavigate();

    const createUser = async(e) =>{
        e.preventDefault();
        const response = await fetch('http://127.0.0.1:8000/login/create/',{
            method:'POST',
            headers:{
                'Content-Type':'application/json'
            },
            body:JSON.stringify({
                'username':e.target.username.value,
                'password':e.target.password.value,
            })
        })
        const data = await response.json()
        console.log(data)
        if(response.status ===201){
            alert(response.status)
            //navigate('/login');
        }else{
            alert(response.status)
        }
    }

    const handleSubmit = (e) => {
        e.preventDefault();
        if (e.target.password.value === e.target.repeat_password.value){
            createUser(e)  
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