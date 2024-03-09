const BASE_URL = 'http://127.0.0.1:8000/';
const jwtToken = localStorage.getItem('authTokens') == null ? null : JSON.parse(localStorage.getItem('authTokens'))['access'];

export async function fetchData2(endpoint) {

  try {
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
  const jwtToken = localStorage.getItem('authTokens') == null ? null : JSON.parse(localStorage.getItem('authTokens'))['access'];
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
  const jwtToken = localStorage.getItem('authTokens') == null ? null : JSON.parse(localStorage.getItem('authTokens'))['access'];
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
  } catch (error) {
      console.error('Error create data:', error);
      throw error;
  }
}

export async function fundPostData(endpoint, user_navigate, body) {
  const jwtToken = localStorage.getItem('authTokens') == null ? null : JSON.parse(localStorage.getItem('authTokens'))['access'];
  try {
    const response = await fetch(`${BASE_URL}${endpoint}`,{
      method:"POST",
      headers:{
        "Content-Type":"application/json",
        "Authorization": `Bearer ${jwtToken}`
      },
      body:JSON.stringify(body)
    });

    if (response.status == 401) {
        alert("Please log in to create fund.");
        user_navigate('/login');  
    } else if (!response.ok) {
        alert("Failed to create fund. Please try again later.");
        console.log(response.status)
        throw new Error('Failed to create fund');   
    } else{
        user_navigate('/');
    }
  } catch (error) {
      console.error('Error create data:', error);
      throw error;
  }
}

export async function userPostData(endpoint, navigate, body) {
  try {
    const response = await fetch(`${BASE_URL}${endpoint}`,{
      method:"POST",
      headers:{
        "Content-Type":"application/json",
      },
      body:JSON.stringify(body)
    });
    if (response.status == 400) {
        alert("A user with that username already exists.");
        navigate('/login');  
    }else if (!response.ok) {
        alert("Failed to create user. Please try again later.");
        throw new Error('Failed to create user');   
    } else{
      navigate('/');
    }
  } catch (error) {
    console.error('Error create data:', error);
    throw error;
  }
}

