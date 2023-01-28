import { useState, useEffect } from 'react'
import React from 'react';

const AddFund = (props) => {
  const [name, setName] = useState([])
  const [currency, setCurrency] = useState([])
  const [aum, setAum] = useState([])

  const requestOptions ={
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify({
      name: name,
      currency: currency,
      aum: aum,
    })
  }

  const handleChange = (event) => {
    const value = event.target.value;
    //event.target.name === "fund" ? setName(value) : setCurrency(value);
    event.target.name === "fund" ? setName(value) : 
    event.target.name === "currency" ? setCurrency(value) : setAum(value); 
  }

  const handleSubmit = (event) => {
    event.preventDefault();
    addFund(requestOptions)
  }

  const addFund = async (requestOptions = '') => {
    const FundsFromServer = await fetchData('http://127.0.0.1:8000/api/fund/', requestOptions)
    props.getFunds()
  }  
  
  const fetchData = async (url, requestOptions = '') => {
    const response = (requestOptions === '') ?  await fetch(url) : await fetch(url,requestOptions);
    const data = await response.json();
    return data; 
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