import React from 'react'
import { useTable, useExpanded, useSortBy, useFilters, useGlobalFilter, useAsyncDebounce } from 'react-table'
import Table from 'react-bootstrap/Table';

const ExtandableRiskTable = (props) => {

    const data = React.useMemo(
        () => props.data,
        [props.data]
      )

    const columns = React.useMemo(
        () => props.columns,
        []
    )

    console.log('COLUMNSSSSSSSSSSSS')
    console.log(columns)

    const {
        getTableProps,
        getTableBodyProps,
        headerGroups,
        rows,
        prepareRow,
        state: { expanded },
    } = useTable({ columns, data}, useExpanded)

    return (
        <>
          <Table striped bordered hover {...getTableProps()}>
            <thead>
              {headerGroups.map(headerGroup => (
                <tr {...headerGroup.getHeaderGroupProps()}>
                  {headerGroup.headers.map(column => (
                    <th {...column.getHeaderProps()}>{column.render('Header')}</th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody {...getTableBodyProps()}>
              {rows.map((row, i) => {
                prepareRow(row)
                return (
                  <tr {...row.getRowProps()}>
                    {row.cells.map(cell => {
                      return <td {...cell.getCellProps()}>{cell.render('Cell')}</td>
                    })}
                  </tr>
                )
              })}
            </tbody>
          </Table>
        </>
      )
}

export default ExtandableRiskTable