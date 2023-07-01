import { useTable, useSortBy, useFilters, useGlobalFilter, useAsyncDebounce } from 'react-table'
//import { useColumns } from 'react-table/columns';
import Table from 'react-bootstrap/Table';
import { useState, useEffect } from 'react'
import React from 'react';
import Form from 'react-bootstrap/Form';

const SideTable = (props) => {

    const data = React.useMemo(
        () => props.data,
        [props.data]
      )

    const columns = React.useMemo(
        () => props.columns,
        []
    )

    //toggleColumn('columnName', false) 

    const {
        getTableProps,
        getTableBodyProps,
        headerGroups,
        rows,
        prepareRow,
    } = useTable({ columns, data }, useSortBy,)

      return (
        <Table style={{ height: '100%', overflow: 'auto' }}>
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

export default SideTable