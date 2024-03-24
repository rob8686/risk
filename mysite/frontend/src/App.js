import React from 'react';
import {BrowserRouter as Router} from 'react-router-dom'
import {Container, Row, Col } from "react-bootstrap";
import TopNavBar from './layout/TopNavBar/TopNavBar.js';
import Sidebar from './layout/Sidebar/Sidebar.js';
import Brand from './layout/Brand/Brand.js';
import { AuthProvider} from './services/AuthContext.js';
import 'bootstrap/dist/css/bootstrap.min.css';
import './layout/Sidebar/sidebar.css';
import AppRoutes from './routes/AppRoutes.js';
import './App.css';


const App = () => {

  const constainerStyle = {
    height: '100vh'
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
                <div>
                  <AppRoutes />
                </div>  
              </Col>  
            </Row>  
          </Container>
        </AuthProvider>
        </Router>
    </div>
  )
}

export default App;

