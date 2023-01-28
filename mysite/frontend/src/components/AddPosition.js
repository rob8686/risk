import { useState, useEffect } from 'react'

const AddPosition = (props) => {
  const [security, setSecurity] = useState([])
  const [quantity, setQuantity] = useState([])
  const [requestFailed, setRequestFailed] = useState([])
  const [percentAum, setPercentAum] = useState([])
  //const [fund, setFund] = useState([])
  const [showAddTask, setShowAddTask] = useState(false)

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

  const handleSubmit =  async (event) => {
    event.preventDefault();
    addPosition(requestOptions);

  }

  const addPosition = async (requestOptions = '') => {
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