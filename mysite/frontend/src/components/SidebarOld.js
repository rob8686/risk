import {Nav} from "react-bootstrap";
import { withRouter } from "react-router";
import '../../static/css/sidebar.css'
//import 'bootstrap/dist/css/bootstrap.min.css';

const Sidebar = (props) => {
  return (
    <div>
        <Nav className="col-md-12 d-none d-md-block bg-light sidebar"
            activeKey="/home"
            onSelect={selectedKey => alert(`selected ${selectedKey}`)}
            >
            <div className="sidebar-sticky"></div>
            <Nav.Item>
                <Nav.Link href="/">Active</Nav.Link>
            </Nav.Item>
            <Nav.Item>
                <Nav.Link eventKey="link-1">Link</Nav.Link>
            </Nav.Item>
            <Nav.Item>
                <Nav.Link eventKey="link-2">Link</Nav.Link>
            </Nav.Item>
        </Nav>   
    </div>
  )
}

export default Sidebar