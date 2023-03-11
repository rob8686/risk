import { Link, useLocation } from 'react-router-dom'
import { Navbar, Nav, NavItem } from 'react-bootstrap';
import { AiOutlineHome, AiOutlinePlus, AiFillHome } from 'react-icons/ai'
import '../../static/css/sidebar.css'
import 'bootstrap/dist/css/bootstrap.min.css';
import * as FaIcons from 'react-icons/fa';
import * as AiIcons from 'react-icons/ai';
import * as IoIcons from 'react-icons/io';
import { IconContext } from 'react-icons';

const Sidebar = (props) => {

    const location = useLocation();  
    console.log('PATHNAME!!!!!!!!!!!!!!!!!!!!')
    console.log(location.pathname)
    
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
        {
          title: 'Products',
          path: '/products',
          icon: <FaIcons.FaCartPlus />,
          cName: 'nav-text'
        },
        {
          title: 'Team',
          path: '/team',
          icon: <IoIcons.IoMdPeople />,
          cName: 'nav-text'
        },
        {
          title: 'Messages',
          path: '/messages',
          icon: <FaIcons.FaEnvelopeOpenText />,
          cName: 'nav-text'
        },
        {
          title: 'Support',
          path: '/support',
          icon: <IoIcons.IoMdHelpCircle />,
          cName: 'nav-text'
        }
      ],
      'CreateFundSidebarData' : [
        {
          title: 'Home',
          path: '/',
          icon: <AiOutlineHome/>,
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
      ]    
    };

    const SidebarType = location.pathname === '/' ? 'HomeSidebarData' : 
    location.pathname === '/login' ? 'LoginSidebarData' :
    location.pathname === '/create_fund' ? 'CreateFundSidebarData' :
    location.pathname === '/positions' ? 'PosiitonsSidebarData' : 'HomeSidebarData'

    const divStyle = {
        backgroundColor: '#f5f5f5', // set your desired background color here
        height: "100%",
        // you can also set other styles such as padding, margin, etc. here
      };
    
    console.log('HERE YOU')
    console.log(SidebarData)
    console.log(SidebarData[SidebarType])

  return (
    <div style={divStyle}>
      <IconContext.Provider value={{}}>
        <nav>
            {SidebarData[SidebarType].map((item, index) => {
              return (
                <Link to={item.path}>
                    <div key={index} className={item.cName}>
                        {item.icon}<br />
                        <span>{item.title}</span>
                    </div>
                </Link>
              );
            })}
        </nav>
      </IconContext.Provider>
    </div>
  )
}

export default Sidebar