import { createContext, useState, useEffect } from "react";
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext()

export default AuthContext;

export const AuthProvider = ({children}) => {
    localStorage.getItem('authTokens')
    const navigate = useNavigate();
    const [authTokens, setAuthTokens] = useState(()=> localStorage.getItem('authTokens') ? JSON.parse(localStorage.getItem('authTokens')) : null)
    const [user, setUser] = useState(()=> localStorage.getItem('authTokens') ? JSON.parse(localStorage.getItem('authTokens')) : null)

    const loginUser = async(e) =>{
        e.preventDefault();
        //console.log('Form SUbmitted');
        //alert("Hello! I am an alert box!");
        const response = await fetch('http://127.0.0.1:8000/login/api/token/',{
            method:'POST',
            headers:{
                'Content-Type':'application/json'
            },
            body:JSON.stringify({'username':e.target.username.value,'password':e.target.password.value})
        })
        const data = await response.json()
        console.log(data)
        if(response.status ===200){
            setAuthTokens(data)
            setUser(e.target.username.value)
            localStorage.setItem('authTokens', JSON.stringify(data))
            localStorage.setItem('user', user)
            navigate('/');
        }else{
            alert(response.status)
        }
    }

    let logoutUser = () => {
        setAuthTokens(null)
        setUser(null)
        localStorage.removeItem('authTokens')
        localStorage.removeItem('user')
        navigate('/');
    }

    const contextData = {
        user:user,
        authTokens:authTokens,
        loginUser:loginUser,
        logoutUser: logoutUser
    }

    return(
        <AuthContext.Provider value={contextData}>
            {children}    
        </AuthContext.Provider>
    )
}