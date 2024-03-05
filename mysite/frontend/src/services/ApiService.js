const BASE_URL = 'http://127.0.0.1:8000/';
const jwtToken = localStorage.getItem('authTokens') == null ? null : JSON.parse(localStorage.getItem('authTokens'))['access'];
console.log('JWT JEWT')
console.log(jwtToken)

export async function fetchData2(endpoint) {

  try {
    console.log('NEW RESPOSNE')
    console.log(`${BASE_URL}${endpoint}`)
    const response = await fetch(`${BASE_URL}${endpoint}`);
    if (!response.ok) {
      throw new Error('Failed to fetch data');
    }
    console.log(response.status)
    return await response.json();
  } catch (error) {
    throw error;
  }
}

export async function deleteData2(endpoint) {

  try {
    const response = await fetch(`${BASE_URL}${endpoint}`,{
      method:"DELETE",
      headers:{
        "Content-Type":"application/json",
        "Authorization": `Bearer ${jwtToken}`
      }
    });
    console.log(response.status)
    if (([401, 403].includes(response.status))) {
      alert("Only the fund owner can delete positions.");    
    } else if (!response.ok) {
      alert("Failed to delete. Please try again later.");
      console.log(response.status)
      throw new Error('Failed to delete data');   
    }
  } catch (error) {
    console.error('Error delete data:', error);
    throw error;
  }
}

export async function positionPostData(endpoint, body, getPosition) {

  try {
    const response = await fetch(`${BASE_URL}${endpoint}`,{
      method:"POST",
      headers:{
        "Content-Type":"application/json",
        "Authorization": `Bearer ${jwtToken}`
      },
      body:JSON.stringify(body)
    });
    if (([401, 403].includes(response.status))) {
        alert("Only the fund owner can create positions.");  
    } else if (!response.ok) {
      alert("Failed to create position. Please try again later.");
      console.log(response.status)
      throw new Error('Failed to create position');   
    } else{
      getPosition(body['fund'])
    }
    console.log('DELEETED!!!!!!')
  } catch (error) {
    console.error('Error create data:', error);
    throw error;
  }
}

export async function fundPostData(endpoint, navigate, body) {

  try {
    const response = await fetch(`${BASE_URL}${endpoint}`,{
      method:"POST",
      headers:{
        "Content-Type":"application/json",
        "Authorization": `Bearer ${jwtToken}`
      },
      body:JSON.stringify(body)
    });
    console.log('response response')
    console.log(response)
    console.log('JWT JEWT')
    console.log(jwtToken)
    console.log(body)
    if (response.status == 401) {
        alert("Please log in to create fund.");
        navigate('/login');  
    } else if (!response.ok) {
      alert("Failed to create fund. Please try again later.");
      console.log(response.status)
      throw new Error('Failed to create fund');   
    } else{
      navigate('/');
    }
    console.log('DELEETED!!!!!!')
  } catch (error) {
    console.error('Error create data:', error);
    throw error;
  }
}

