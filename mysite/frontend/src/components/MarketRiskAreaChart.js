import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer, AreaChart, Area } from 'recharts';

import React from 'react'

const MarketRiskAreaChart = (props) => {
  return (
    <div>
      <ResponsiveContainer width="100%" height="100%" aspect={1.6}>
      <AreaChart
        width={500}
        height={300}
        data={props.data}
        margin={{
          top: 5,
          right: 30,
          left: 20,
          bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="category"dataKey="bin"/>
        <YAxis />
        <Tooltip />
        <Legend />
        <Area type="monotone" dataKey="count" stroke="#8884d8" fill="#8884d8" />

      </AreaChart>
      </ResponsiveContainer>
  </div>
  )
  }

export default MarketRiskAreaChart