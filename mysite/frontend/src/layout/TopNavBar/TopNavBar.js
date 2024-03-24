import React, {useContext} from 'react'
import Container from 'react-bootstrap/Container';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import NavDropdown from 'react-bootstrap/NavDropdown';
import {Link} from 'react-router-dom'
import AuthContext from '../../services/AuthContext.js';

const TopNavBar = () => {

    const {user, userName, logoutUser} = useContext(AuthContext)

    const navStyle = {
      backgroundColor: '#3b4054',
    };

    const linkStyle = {
      textDecoration: 'none',
      color: 'white',
    };

    console.log("USER!!!!!!!")
    console.log(userName)

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
                    <Link to="/login" style={linkStyle} className="nav-link link_formatted">Login</Link>
                  </Nav.Item>
                  <Nav.Item>                    
                    <Link to="/create_user" style={linkStyle}  className="nav-link link_formatted">Create Account</Link>
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

