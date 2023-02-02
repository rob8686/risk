import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import React, { useState } from 'react';

const RiskLineChart = (props) => {

    const [data, setData] = useState([props.data]);
    
    return (//aspect={1.6}

      <ResponsiveContainer width="100%" height="100%" aspect={1.6}>
        <LineChart
          width={900}
          height={400}
          data={props.data}
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
  )
}

export default RiskLineChart