import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Label } from 'recharts';

const RiskLineChart = (props) => {

    return (
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
          <XAxis dataKey={props.dataKey}>
            <Label value={props.xlabel} offset={0} position="insideBottom" />
          </XAxis>  
          <YAxis label={{ value: props.ylabel, angle: -90, position: 'insideLeft' }}/>
          <Tooltip />
          <Legend verticalAlign="top"/>
          {props.lines.map((line)=>{
            return line
          })}
        </LineChart>
      </ResponsiveContainer>
  )
}

export default RiskLineChart