import { useState, useEffect } from 'react'

const TableInput = (props) => {
    const [quantity, setQuantity] = useState([])

    const handleSubmit = (event) => {
        event.preventDefault();
        updatePosition(props.positionNum)
        }

    const handleChange = (event) => {
        const value = event.target.value;
        setQuantity(value);
        }

    const updatePosition = async (positionNum) => {
        const updateRequestOptions ={
            method:"PATCH",
            headers:{"Content-Type":"application/json"},
            body: JSON.stringify({
                quantity: quantity
              })
        }
        const requestOptions ={
            method:"UPDATE",
            headers:{"Content-Type":"application/json"},
            body: JSON.stringify({
              security: 'TTWO',
              quantity: quantity,
              fund: '1'
            })
          }
        const FundsFromServer = await props.fetchData(`http://127.0.0.1:8000/api/position/${props.positionNum}/`, updateRequestOptions)
        }  

  return (
    <div>
        <form onSubmit={handleSubmit}>
            <input type='number' placeholder={props.value} onChange={handleChange}/>
            <input type="submit" value="Update"/>
        </form>
    </div>
  )
}

export default TableInput