import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

import React from 'react'

const PivotBarChart = (props) => {
  return (
    <div>
      <BarChart
        width={500}
        height={300}
        data={props.data}
        layout="vertical" barCategoryGap={1}
        margin={{
          top: 5,
          right: 30,
          left: 20,
          bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number"/>
        <YAxis dataKey={props.dataKey} type="category"/>
        <Tooltip />
        <Legend />
        {props.bar}
      </BarChart>
      
</div>
)
}

export default PivotBarChart