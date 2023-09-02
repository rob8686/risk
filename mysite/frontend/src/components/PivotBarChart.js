import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer } from 'recharts';

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
        <XAxis type="number" domain={([dataMin, dataMax]) => { const absMax = Math.max(Math.abs(dataMin), Math.abs(dataMax)); return [-absMax, absMax]; }} />
        <YAxis dataKey={props.dataKey} type="category"/>
        <Tooltip />
        <Legend />
        <ReferenceLine x={0} stroke="#000" />
        <Bar dataKey="perc_contrib" fill="#8884d8" barSize={20} rowHeight={30}>
        {props.data.map((datum, entry, index) => (
          //https://stackoverflow.com/questions/62701150/positive-negative-bar-chart-color-w-recharts
            <Cell
                key={`cell-${index}`}
                fill={
                    datum["perc_contrib"] > 0
                        ? 'green'
                        : 'red'
                }
            />
        ))}  
        </Bar>
      </BarChart>
      
  </div>
  )
  }

export default PivotBarChart