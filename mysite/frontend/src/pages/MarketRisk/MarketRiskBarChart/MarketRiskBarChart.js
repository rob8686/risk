import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer } from 'recharts';

import React from 'react'

const MarketRiskBarChart = (props) => {
  return (
    <div>
      <ResponsiveContainer width="100%" height="100%" aspect={1.6}>
      <BarChart
        width={500}
        height={300}
        data={props.data}
        barCategoryGap={1}
        margin={{
          top: 5,
          right: 30,
          left: 20,
          bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={props.axis}/>
        <YAxis/>
        <Tooltip />
        <Legend />
        <ReferenceLine x={0} stroke="#000" />
        <Bar dataKey={props.bar}> 
        {props.data.map((datum, entry, index) => (
          //https://stackoverflow.com/questions/62701150/positive-negative-bar-chart-color-w-recharts
            <Cell
                key={`cell-${index}`}
                fill={
                    datum[props.bar] > 0
                        ? 'green'
                        : 'red'
                }
            />
        ))}
        </Bar>
      </BarChart>
      </ResponsiveContainer>
  </div>
  )
  }

export default MarketRiskBarChart