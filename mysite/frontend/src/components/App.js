import React from 'react';
import { useState, useEffect, useContext } from 'react'
import {BrowserRouter as Router, Switch, Route, Routes, Link, Redirect, useLocation} from 'react-router-dom'
import {Container, Row, Col, Card, Form, Button } from "react-bootstrap";
import ReactDOM from 'react-dom';
import { render } from "react-dom";
import Funds from './Funds.js';
import Positions from './Positions.js';
import Liquidity from './Liquidity.js';
import Performance from './Performance.js';
import MarketRisk from './MarketRisk.js';
import TopNavBar from './TopNavBar.js';
import Sidebar from './Sidebar';
import Login from './Login.js';
import CreateUser from './CreateUser.js';
import CreateFund from './CreateFund.js';
import Brand from './brand.js';
import { AuthProvider} from './AuthContext.js';
import 'bootstrap/dist/css/bootstrap.min.css';
import '../../static/css/sidebar.css'
import { AiOutlineHome, AiFillHome } from 'react-icons/ai';
import CreatePosition from './CreatePosition.js';
import './App.css';
import {fetchData2} from '../services/ApiService.js'


const App = () => {

  const [funds, setFunds] = useState([])
  const [pathname, setPathname] = useState([window.location.pathname])
  const currentURL = window.location.href // returns the absolute URL of a page

  const constainerStyle = {
    //backgroundColor: '#3b4054', // set your desired background color here
    height: '100vh'
    // you can also set other styles such as padding, margin, etc. here
  };

  const divStyle = {
    //backgroundColor: '#3b4054', // set your desired background color here
    //boxShadow: '5px 5px 5px',
    //margin: '120px',
    //padding: '10px',
    //border: '5px solid red',
    // backgroundColor: 'white',
    // you can also set other styles such as padding, margin, etc. here
  };

  return (
    <div>
        <Router>  
        <AuthProvider>
          <Container fluid style={constainerStyle}>
            <Row className='white-btm-brdr'>
              <Col style={{ padding: 0 }} xs={1}>      
                <Brand/>
              </Col>
              <Col style={{ paddingLeft: 0, paddingRight: 0}}>      
                <TopNavBar/>
              </Col>
            </Row>
            <Row>
              <Col style={{ padding: 0 }} xs={1} lg={.5}>      
                <Sidebar />
              </Col>
              <Col id="page-content-wrapper" style={{ paddingTop: 20 }}>
                <div style={divStyle}>
                  <Routes>
                    <Route path="/" element={<Funds data={funds}/>}/>
                    <Route path="/create_fund" element={<CreateFund />}/>
                    <Route path="/positions/:id" element={<Positions/>}/>
                    <Route path="/liquidity/:id/:date" element={<Liquidity/>}/>
                    <Route path="/performance/:id/:date" element={<Performance/>}/>
                    <Route path="/market_risk/:id/:date" element={<MarketRisk/>}/>
                    <Route path="/login" element={<Login/>}/>
                    <Route path="/create_user" element={<CreateUser/>}/>
                    <Route path="/create_position/*" element={<CreatePosition/>}/>
                  </Routes>
                </div>  
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
