import React, {useContext} from 'react'
import Container from 'react-bootstrap/Container';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import NavDropdown from 'react-bootstrap/NavDropdown';
import {Link} from 'react-router-dom'
import AuthContext from './AuthContext.js';

const TopNavBar = () => {

    const {user, logoutUser} = useContext(AuthContext)

    const navStyle = {
      backgroundColor: '#3b4054', // set your desired background color here
      color: 'white'
    };

    const linkStyle = {
      textDecoration: 'none',
      color: 'white',
    };

    //<Navbar bg="light" variant="light" expand="lg"></Navbar>
    //<Navbar.Brand href="#home">React-Bootstrap</Navbar.Brand>

    return (
        <Navbar style={navStyle} expand="lg">
          <Container>
            <Navbar.Toggle aria-controls="basic-navbar-nav" />
            <Navbar.Collapse className="justify-content-end">
              <Navbar.Text>
                {user ? (
                 <p  onClick={logoutUser}>Logout</p>
                ): (
                <Link to="/login" stlye={linkStyle}>Login</Link>
                )}
              </Navbar.Text>
            </Navbar.Collapse>
          </Container>
        </Navbar>
      );
}

export default TopNavBar

