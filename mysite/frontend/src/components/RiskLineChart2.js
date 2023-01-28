
import React, { useState, PureComponent } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';


const RiskLineChart2 = (props) => {

  const [data, setData] = useState([props.data]);

  return (//aspect={1.6}
    <div style={{height:'100px',width:'100px'}}>
    <div style={{height:'100%',width:'100%'}}>
    <ResponsiveContainer width="99%" aspect={3}>
      <LineChart
        width={900}
        height={400}
        data={data}
        margin={{
          top: 5,
          right: 30,
          left: 20,
          bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={props.dataKey} />
        <YAxis />
        <Tooltip />
        <Legend />
        {props.lines.map((line)=>{
          return line
        })}
      </LineChart>
    </ResponsiveContainer>
    </div>
    </div>
  )
}

export default RiskLineChart2