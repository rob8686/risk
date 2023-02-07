import { createContext, useState, useEffect } from "react";

const AuthContext = createContext()

export default AuthContext;

export const AuthProvider = ({children}) => {
    //http://127.0.0.1:8000/login/api/token/
    const [authTokens, setAuthTokens] = useState(null)
    const [user, setUser] = useState(null)

    const loginUser = async(e) =>{
        e.preventDefault();
        //console.log('Form SUbmitted');
        //alert("Hello! I am an alert box!");
        const response = await fetch('http://127.0.0.1:8000/login/api/token/',{
            method:'POST',
            headers:{
                'Content-Type':'application/json'
            },
            body:JSON.stringify({'username':e.target.username,'password':e.target.password})
        })
        const data = await response.json()
        console.log(data)
    }

    const contextData = {
        loginUser:loginUser
    }

    return(
        <AuthContext.Provider value={contextData}>
            {children}    
        </AuthContext.Provider>
    )
}