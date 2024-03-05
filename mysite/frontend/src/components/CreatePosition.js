import {Container, Row, Col, Form, Button, InputGroup } from "react-bootstrap";
import { useNavigate, useLocation } from 'react-router-dom';
import {positionPostData} from '../services/ApiService.js'

const CreatePosition = (props) => {

    const location = useLocation(); 
    const fundNum = location.pathname.split('/').pop()


    const handleSubmit = async(e) => {
        e.preventDefault();
        await positionPostData('api/position/',{security: e.target.ticker.value, fund: fundNum, percent_aum: e.target.percAum.value}, props.getPositions)
    }  


    return (
        <Container fluid>
        <div className='content' style={{ display: 'inline-flex', fontSize: '8px !important', padding:0,margin:0,marginTop:1}}>
            <Form onSubmit={handleSubmit}>
                <Row xs="auto" className='content' style={{ padding:0,margin:0 }}>
                    <Col>
                        <h5>Create Position</h5>
                    </Col>  
                    <Col>
                        <Form.Group className="mb-2" controlId="formBasicFundName" >
                            <Form.Control size="sm" type="text" name="ticker" placeholder="Ticker" />
                        </Form.Group>
                    </Col>
                    <Col>    
                        <InputGroup size="sm" className="mb-2">
                            <Form.Control placeholder="% AUM" name="percAum" />
                            <InputGroup.Text>%</InputGroup.Text>
                        </InputGroup>
                    </Col>
                    <Col>
                        <Button size="sm" variant="primary" type="submit">
                            Submit
                        </Button>
                    </Col>
                </Row>
            </Form>
        </div>
        </Container>
    )
    }

export default CreatePosition