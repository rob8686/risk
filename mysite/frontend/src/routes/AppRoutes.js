import {Route, Routes} from 'react-router-dom'
import Funds from '../pages/Funds/Funds.js';
import Login from '../pages/Login/Login.js';
import CreateUser from '../pages/CreateUser/CreateUser.js';
import CreateFund from '../pages/CreateFund/CreateFund.js';
import Positions from '../pages/Positions/Positions.js';
import Liquidity from '../pages/Liquidity/Liquidity.js';
import Performance from '../pages/Performance/Performance.js';
import MarketRisk from '../pages/MarketRisk/MarketRisk.js';



const AppRoutes = () => {
  return (
    <Routes>
        <Route path="/" element={<Funds/>}/>
        <Route path="/create_fund" element={<CreateFund />}/>
        <Route path="/positions/:id" element={<Positions/>}/>
        <Route path="/liquidity/:id/:date" element={<Liquidity/>}/>
        <Route path="/performance/:id/:date" element={<Performance/>}/>
        <Route path="/market_risk/:id/:date" element={<MarketRisk/>}/>
        <Route path="/login" element={<Login/>}/>
        <Route path="/create_user" element={<CreateUser/>}/>
    </Routes>
  )
}

export default AppRoutes