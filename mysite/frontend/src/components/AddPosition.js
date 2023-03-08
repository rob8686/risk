import { useState, useEffect, useContext } from 'react'
import AuthContext from './AuthContext.js'
import { useNavigate } from 'react-router-dom';

const AddPosition = (props) => {
  const navigate = useNavigate();
  const [security, setSecurity] = useState([])
  const [quantity, setQuantity] = useState([])
  const [requestFailed, setRequestFailed] = useState([])
  const [percentAum, setPercentAum] = useState([])
  //const [fund, setFund] = useState([])
  const [showAddTask, setShowAddTask] = useState(false)
  const {authTokens, logoutUser} = useContext(AuthContext)
  

  const addPosition = async() =>{
    let response = await fetch('http://127.0.0.1:8000/api/position/', {
        method:'POST',
        headers:{
            'Content-Type':'application/json',
            'Authorization':'Bearer ' + String(authTokens.access)
        },
        body: JSON.stringify({
          security: security,
          quantity: quantity,
          fund: props.fundNum[0],
          percent_aum: percentAum 
        })
    })
    let data = await response.json()
  
    if(response.status === 201){
        props.getPositions(props.fundNum)
        alert('Position Created')
    }else if(response.statusText === 'Unauthorized'){
        alert(data.code)
    }
    
  }

  const requestOptions ={
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify({
      security: security,
      quantity: quantity,
      fund: props.fundNum[0],
      percent_aum: percentAum 
    })
  }

  const handleChange = (event) => {
    const value = event.target.value;
    event.target.name === "security" ? setSecurity(value) : 
    event.target.name === "quantity" ? setQuantity(value): setPercentAum(value);
  }

  const handleSubmit2 =  async (event) => {
    event.preventDefault();
    addPosition(requestOptions);

  }

  const handleSubmit = (event) => {
    event.preventDefault();
    if (authTokens){
      addPosition()  
    }
    else{
      navigate('/login');
    }
  }

  const addPosition2 = async (requestOptions = '') => {
    const FundsFromServer = await fetchData('http://127.0.0.1:8000/api/position/', requestOptions)
    props.getPositions(props.fundNum)
  }  
  
  const fetchData = async (url, requestOptions = '') => {
    const response = (requestOptions === '') ?  await fetch(url) : await fetch(url,requestOptions)
    .then((response) => {
      if(!response.ok) throw new Error(response.status);
      else return response.json();
    })
    .catch((error) => {
      console.log('error: ' + error);
      setRequestFailed(true)
    });
    
  }
  
  return (
    <div>
      <form onSubmit={handleSubmit}>
          <div>
              <label>Ticker</label>
              <input type='text'name='security' onChange={handleChange}></input>
          </div>
          <div>
              <label>Quantity</label>
              <input type='number' name='quantity' onChange={handleChange}></input>
          </div>
          <div>
            <label>% AUM</label>
            <input type='number' name="percent_aum" onChange={handleChange}></input>
        </div>

          <input type='submit' value='Add Position'></input>
      </form>
    {requestFailed ? <p>Invalid Ticker</p> : <p></p>}
    </div>
  )
}

export default AddPosition