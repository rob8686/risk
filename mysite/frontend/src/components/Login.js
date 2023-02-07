import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import AuthContext from './AuthContext.js';
import { useContext } from 'react';

const onSubmit = (event) => {
    console.log("Hello World!!!!!!!!!")
    event.preventDefault();
}

const Login = () => {
  const {loginUser} = useContext(AuthContext)  
  console.log('hereeeeeee')
  return (
    <Form onSubmit={loginUser}>
        <Form.Group className="mb-3" controlId="formBasicUserName" >
            <Form.Label>Username</Form.Label>
            <Form.Control type="text" name="username" placeholder="Username" />
        </Form.Group>
        <Form.Group className="mb-3" controlId="formBasicPassword">
            <Form.Label>Password</Form.Label>
            <Form.Control type="password" name="password" placeholder="Password" />
        </Form.Group>
        <Button variant="primary" type="submit">
            Submit
        </Button>
  </Form>
  )
}

export default Login