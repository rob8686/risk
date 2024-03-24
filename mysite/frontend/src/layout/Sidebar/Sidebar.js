import { Link, useLocation, useParams } from 'react-router-dom'
import { Navbar, Nav, NavItem } from 'react-bootstrap';
import { AiOutlineHome, AiOutlinePlus, AiFillHome } from 'react-icons/ai'
import './sidebar.css'
import 'bootstrap/dist/css/bootstrap.min.css';
import * as FaIcons from 'react-icons/fa';
import * as AiIcons from 'react-icons/ai';
import * as IoIcons from 'react-icons/io';
import { IconContext } from 'react-icons';

const Sidebar = (props) => {

    const location = useLocation();  
    
    const SidebarData = 
    {
      'HomeSidebarData' : [
        {
          title: 'Home',
          path: '/',
          icon: <AiOutlineHome/>,
          cName: 'nav-text'
        },
        {
          title: 'Add Fund',
          path: '/create_fund',
          icon: <AiOutlinePlus />,
          cName: 'nav-text'
        },
      ],
      'CreateFundSidebarData' : [
        {
          title: 'Home',
          path: '/',
          icon: <AiOutlineHome/>,
          cName: 'nav-text'
        },
      ],
      'PositionsSidebarData' : [
        {
          title: 'Home',
          path: '/',
          icon: <AiOutlineHome/>,
          cName: 'nav-text'
        },
        {
          title: 'Add Position',
          path: '/create_position/' + location.pathname.split('/').pop(),
          icon: <AiOutlinePlus />,
          cName: 'nav-text'
        },
      ],
      'LoginSidebarData' : [
        {
          title: 'Home',
          path: '/',
          icon: <AiOutlineHome/>,
          cName: 'nav-text'
        },
      ],
      'CreatePositionSidebarData' : [
        {
          title: 'Home',
          path: '/',
          icon: <AiOutlineHome/>,
          cName: 'nav-text'
        },
      ]     
    };

    const SidebarType = location.pathname === '/' ? 'HomeSidebarData' : 
    location.pathname === '/login' ? 'LoginSidebarData' :
    location.pathname === '/create_fund' ? 'CreateFundSidebarData' :
    location.pathname.split('/')[1] === 'create_position' ? 'CreatePositionSidebarData' :
    location.pathname.split('/')[1] === 'positions' ? 'PositionsSidebarData' : 'HomeSidebarData'

    let { id } = useParams();
    const params = useParams();
    console.log(id)
    console.log(params)

    const divStyle = {
        backgroundColor: '#3b4054', 
        minHeight:'100vh',
        height: '100%',
      };

    const linkStyle = {
      textDecoration: 'none',
      color: 'white',
    };
    
  return (
    <div style={divStyle}>
      <IconContext.Provider value={{}}>
        <nav>
            {SidebarData[SidebarType].map((item, index) => {
              return (
                <div style={{textAlign: 'center'}}>
                  <Link to={item.path} style={linkStyle}>
                      <div key={index} className={item.cName}>
                          {item.icon}<br />
                          <span>{item.title}</span>
                      </div>
                  </Link>
                </div>
              );
            })}
        </nav>
      </IconContext.Provider>
    </div>
  )
}

export default Sidebar