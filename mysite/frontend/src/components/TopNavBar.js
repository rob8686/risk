import React, {useContext} from 'react'
import Container from 'react-bootstrap/Container';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import NavDropdown from 'react-bootstrap/NavDropdown';
import {Link} from 'react-router-dom'
import AuthContext from './AuthContext.js';

const TopNavBar = () => {

    const {user, userName, logoutUser} = useContext(AuthContext)

    const navStyle = {
      backgroundColor: '#3b4054', // set your desired background color here
      //color: 'white'
    };

    const linkStyle = {
      //textDecoration: 'none',
      //color: 'red !important',
    };

    console.log("USER!!!!!!!")
    console.log(userName)

    //<p  stlye={linkStyle} className='link_formatted' onClick={logoutUser}>Logout</p> 

    return (
        <Navbar style={navStyle} expand="lg">
          <Container fluid>
            <Navbar.Collapse className="justify-content-end">
              <Navbar.Text>
                {user ? (
                 <Nav className="me-auto">
                  <Nav.Item className="nav-link link_formatted">                    
                    Hello {userName}
                  </Nav.Item>
                  <Nav.Item className="nav-link link_formatted" style={{'cursor': 'pointer'}} onClick={logoutUser}>                    
                    Logout
                  </Nav.Item>
                 </Nav>
                ): (
                <Nav className="me-auto">
                  <Nav.Item>                    
                    <Link to="/login" className="nav-link link_formatted">Login</Link>
                  </Nav.Item>
                  <Nav.Item>                    
                    <Link to="/create_user" className="nav-link link_formatted">Create Account</Link>
                  </Nav.Item>
                </Nav>
                )}
              </Navbar.Text>
            </Navbar.Collapse>
          </Container>
        </Navbar>
      );
}

export default TopNavBar

