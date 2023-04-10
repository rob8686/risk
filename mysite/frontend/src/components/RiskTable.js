import { useTable, useSortBy, useFilters, useGlobalFilter, useAsyncDebounce } from 'react-table'
import Table from 'react-bootstrap/Table';
import classnames from 'classnames';
import { useState, useEffect } from 'react'
import React from 'react';
import Form from 'react-bootstrap/Form';

const RiskTable = (props) => {

    const styleArray = props.style.split(' ');

    function DefaultColumnFilter({
        column: { filterValue, preFilteredRows, setFilter },
      }) {
        const count = preFilteredRows.length
      
        //<Form.Control size="sm" type="text" placeholder="Small text" />

        return (
          // change back to input and remove the first 
          <Form.Control
            size="sm"
            type="text"
            style={{ width: "80%" }}
            value={filterValue || ''}
            onChange={e => {
              setFilter(e.target.value || undefined) // Set undefined to remove the filter entirely
            }}
            //placeholder={`Search ${count} records...`}
          />
        )
      }

    const defaultColumn = React.useMemo(
        () => ({
          // Let's set up our default Filter UI
          Filter: DefaultColumnFilter,
        }),
        []
      )

    const data = React.useMemo(
        () => props.data,
        [props.data]
      )

    const columns = React.useMemo(
        () => props.columns,
        []
    )



    const {
        getTableProps,
        getTableBodyProps,
        headerGroups,
        rows,
        prepareRow,
    } = useTable({ columns, data, defaultColumn }, useFilters, useSortBy,)

      return (
        <Table 
            {...getTableProps()} className={props.style}
            striped={styleArray.includes('striped')}
            bordered={styleArray.includes('bordered')}
            hover={styleArray.includes('hover')}
            responsive= {styleArray.includes('responsive')}
            tableSm= {styleArray.includes('table-sm')}
        >
          <thead>
            {headerGroups.map(headerGroup => (
              <tr {...headerGroup.getHeaderGroupProps()}>
                {headerGroup.headers.map(column => (
                  <th {...column.getHeaderProps(column.getSortByToggleProps())}>
                    {column.render('Header')}
                    <span>
                    {column.isSorted
                      ? column.isSortedDesc
                        ? ' 🔽'
                        : ' 🔼'
                      : ''}
                  </span>
                  <div>{column.canFilter ? column.render('Filter') : null}</div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody {...getTableBodyProps()}>
            {rows.map(row => {
              prepareRow(row)
              return (
                <tr {...row.getRowProps()}>
                  {row.cells.map(cell => {
                    return (
                      <td>
                        {cell.render('Cell')}
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </Table>
      )
}

export default RiskTable