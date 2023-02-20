import { useState, useEffect, useContext } from 'react'
import React from 'react';
import AuthContext from './AuthContext.js'
import { useNavigate } from 'react-router-dom';

const AddFund = (props) => {
  const navigate = useNavigate();
  const [name, setName] = useState([])
  const [currency, setCurrency] = useState([])
  const [aum, setAum] = useState([])
  const {authTokens, logoutUser} = useContext(AuthContext)

  const addFund = async() =>{
    let response = await fetch('http://127.0.0.1:8000/api/fund/', {
        method:'POST',
        headers:{
            'Content-Type':'application/json',
            'Authorization':'Bearer ' + String(authTokens.access)
        },
        body: JSON.stringify({
          name: name,
          currency: currency,
          aum: aum,
        })
    })
    let data = await response.json()
  
    if(response.status === 201){
        props.getFunds()
        alert('Fund Created')
    }else if(response.statusText === 'Unauthorized'){
        alert(data.code)
    }
    
  }

  const handleChange = (event) => {
    const value = event.target.value;
    event.target.name === "fund" ? setName(value) : 
    event.target.name === "currency" ? setCurrency(value) : setAum(value); 
  }

  const handleSubmit = (event) => {
    event.preventDefault();
    if (authTokens){
      addFund()  
    }
    else{
      navigate('/login');
    }
  }

  return (
    <form onSubmit={handleSubmit}>
        <div>
            <label>Fund Name</label>
            <input type='text'name="fund" onChange={handleChange}></input>
        </div>
        <div>
            <label>Currency</label>
            <input type='text' name="currency" onChange={handleChange}></input>
        </div>
        <div>
            <label>AUM</label>
            <input type='number' name="aum" onChange={handleChange}></input>
        </div>

        <input type='submit' value='Add Fund'></input>
    </form> 
  )
}

export default AddFund