import React from 'react';
import { useState, useEffect, useContext } from 'react'
import {BrowserRouter as Router, Switch, Route, Routes, Link, Redirect} from 'react-router-dom'
import {Container, Row, Col, Card, Form, Button } from "react-bootstrap";
import ReactDOM from 'react-dom';
import { render } from "react-dom";
import Funds from './Funds.js';
import AddFund from './AddFund.js';
import Positions from './Positions.js';
import Liquidity from './Liquidity.js';
import Performance from './Performance.js';
import TopNavBar from './TopNavBar.js';
import Sidebar from './Sidebar';
import Login from './Login.js';
import CreateFund from './CreateFund.js';
import { AuthProvider} from './AuthContext.js';
import 'bootstrap/dist/css/bootstrap.min.css';
import '../../static/css/sidebar.css'
import { AiOutlineHome, AiFillHome } from 'react-icons/ai';

const App = () => {

  const [funds, setFunds] = useState([])

  useEffect(() => {
    getFunds()
  }, []) 

  const getFunds = async () => {
    const FundsFromServer = await fetchData('http://127.0.0.1:8000/api/fund/')
    setFunds(FundsFromServer)
  }

  const fetchData = async (url, requestOptions = '') => {
    const response = (requestOptions === '') ?  await fetch(url) : await fetch(url,requestOptions);
    const data = await response.json();
    return data; 
  }

  return (
    <div>
        <Router>
        <AuthProvider>
          <TopNavBar/>
          <Container fluid>
            <Row>
              <Col xs={1}>      
                <Sidebar />
              </Col>
              <Col id="page-content-wrapper">  
                <Routes>
                  <Route path="/" element={<Funds data={funds} getFunds={getFunds} fetchData={fetchData}/>}/>
                  <Route path="/create_fund" element={<CreateFund/>}/>
                  <Route path="/positions" element={<Positions/>}/>
                  <Route path="/liquidity/:id" element={<Liquidity/>}/>
                  <Route path="/performance/:id" element={<Performance/>}/>
                  <Route path="/login" element={<Login/>}/>
                </Routes>
              </Col>  
            </Row>  
          </Container>
        </AuthProvider>
        </Router>
    </div>
  )
}

const appDiv = document.getElementById("app");
render(<App />, appDiv);
