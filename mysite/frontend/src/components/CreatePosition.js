import {Container, Row, Col, Form, Button, InputGroup } from "react-bootstrap";
import { useNavigate, useLocation } from 'react-router-dom';
import AuthContext from './AuthContext.js';
import { useContext } from 'react';

const CreatePosition = (props) => {

  const {authTokens, logoutUser} = useContext(AuthContext)  
  const navigate = useNavigate();
  const location = useLocation(); 
  const fundNum = location.pathname.split('/').pop()
  
  const createPosition = async(e) =>{
    e.preventDefault();
    const response = await fetch('http://127.0.0.1:8000/api/position/',{
        method:'POST',
        headers:{
            'Content-Type':'application/json',
            'Authorization':'Bearer ' + String(authTokens.access)
        },
        body:JSON.stringify({
             security: e.target.ticker.value,
             fund: fundNum,
             percent_aum: e.target.percAum.value 
        })
    })
    const data = await response.json()
    console.log(fundNum)
    if(response.status ===201){
        alert(response.status)
        props.getPositions(fundNum)
    }else{
        alert(response.status)
    }
    }

    const handleSubmit = (e) => {
        e.preventDefault();
        if (authTokens){
            createPosition(e)  
        }
        else{
            console.log('LOG IN????')
            //navigate('/login');
            alert('Log in to create posiiton')
        }
    }  

  return (
    <Container fluid className='content'> 
        <Form onSubmit={handleSubmit}>
            <Row xs="auto">
                <Col>
                    <Form.Label>Ticker</Form.Label>
                </Col>  
                <Col>
                    <Form.Group className="mb-3" controlId="formBasicFundName" >
                        <Form.Control type="text" name="ticker" placeholder="Ticker" />
                    </Form.Group>
                </Col>
                <Col>
                    <Form.Label>% AUM</Form.Label>
                </Col>
                <Col>    
                    <InputGroup className="mb-3">
                        <Form.Control placeholder="% AUM" name="percAum" />
                        <InputGroup.Text>%</InputGroup.Text>
                    </InputGroup>
                </Col>
                <Col>
                    <Button variant="primary" type="submit">
                        Submit
                    </Button>
                </Col>
            </Row>
        </Form>
  </Container>
  )
}

export default CreatePosition