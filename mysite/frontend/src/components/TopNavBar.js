import React, {useContext} from 'react'
import Container from 'react-bootstrap/Container';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import NavDropdown from 'react-bootstrap/NavDropdown';
import {Link} from 'react-router-dom'
import AuthContext from './AuthContext.js';

const TopNavBar = () => {

    const {user, logoutUser} = useContext(AuthContext)

    return (
        <Navbar bg="dark" variant="dark" expand="lg">
          <Container>
            <Navbar.Brand href="#home">React-Bootstrap</Navbar.Brand>
            <Navbar.Toggle aria-controls="basic-navbar-nav" />
            <Navbar.Collapse className="justify-content-end">
              <Navbar.Text>
                <Link to={'/login'}>
                  login
                </Link>
                {user ? (
                 <p  onClick={logoutUser}>Logout</p>
                ): (
                <Link to="/login" >Login</Link>
                )}
              </Navbar.Text>
            </Navbar.Collapse>
          </Container>
        </Navbar>
      );
}

export default TopNavBar

