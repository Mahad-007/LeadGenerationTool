import { useState, useMemo, useCallback } from 'react'
import { cn } from '@/lib/utils'
import { ChevronUp, ChevronDown, ChevronsUpDown, Loader2 } from 'lucide-react'

export interface Column<T> {
  key: keyof T
  header: string
  sortable?: boolean
  render?: (value: T[keyof T], row: T) => React.ReactNode
  className?: string
}

export interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  rowKey?: keyof T
  loading?: boolean
  emptyMessage?: string
  onRowClick?: (row: T) => void
  className?: string
  'aria-label'?: string
}

type SortDirection = 'asc' | 'desc' | null

export function DataTable<T extends object>({
  data,
  columns,
  rowKey,
  loading = false,
  emptyMessage = 'No data available',
  onRowClick,
  className,
  'aria-label': ariaLabel,
}: DataTableProps<T>) {
  const [sortColumn, setSortColumn] = useState<keyof T | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>(null)

  const handleSort = useCallback((column: Column<T>) => {
    if (!column.sortable) return

    if (sortColumn === column.key) {
      if (sortDirection === 'desc') {
        setSortDirection('asc')
      } else if (sortDirection === 'asc') {
        setSortColumn(null)
        setSortDirection(null)
      }
    } else {
      setSortColumn(column.key)
      setSortDirection('desc')
    }
  }, [sortColumn, sortDirection])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent, column: Column<T>) => {
      if (!column.sortable) return
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        handleSort(column)
      }
    },
    [handleSort]
  )

  const handleRowKeyDown = useCallback(
    (e: React.KeyboardEvent, row: T) => {
      if (!onRowClick) return
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        onRowClick(row)
      }
    },
    [onRowClick]
  )

  const sortedData = useMemo(() => {
    if (!sortColumn || !sortDirection) return data

    return [...data].sort((a, b) => {
      const aValue = a[sortColumn]
      const bValue = b[sortColumn]

      if (aValue === bValue) return 0
      if (aValue === null || aValue === undefined) return 1
      if (bValue === null || bValue === undefined) return -1

      const comparison = aValue < bValue ? -1 : 1
      return sortDirection === 'asc' ? comparison : -comparison
    })
  }, [data, sortColumn, sortDirection])

  const getRowKey = (row: T, index: number): string => {
    if (rowKey && row[rowKey] !== undefined) {
      return String(row[rowKey])
    }
    return String(index)
  }

  const getAriaSort = (column: Column<T>): 'ascending' | 'descending' | 'none' | undefined => {
    if (!column.sortable) return undefined
    if (sortColumn !== column.key) return 'none'
    return sortDirection === 'asc' ? 'ascending' : 'descending'
  }

  if (loading) {
    return (
      <div
        data-testid="table-loading"
        className="flex items-center justify-center py-12"
        role="status"
        aria-label="Loading table data"
      >
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" aria-hidden="true" />
        <span className="sr-only">Loading...</span>
      </div>
    )
  }

  return (
    <div className={cn('overflow-x-auto', className)}>
      <table
        className="min-w-full divide-y divide-gray-200"
        aria-label={ariaLabel}
      >
        <thead className="bg-gray-50">
          <tr>
            {columns.map((column) => (
              <th
                key={String(column.key)}
                scope="col"
                aria-sort={getAriaSort(column)}
                tabIndex={column.sortable ? 0 : undefined}
                className={cn(
                  'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider',
                  column.sortable && 'cursor-pointer select-none hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset',
                  column.className
                )}
                onClick={() => handleSort(column)}
                onKeyDown={(e) => handleKeyDown(e, column)}
              >
                <div className="flex items-center gap-1">
                  {column.header}
                  {column.sortable && (
                    <span className="inline-flex flex-col" aria-hidden="true">
                      {sortColumn === column.key ? (
                        sortDirection === 'asc' ? (
                          <ChevronUp
                            data-testid="sort-indicator"
                            className="h-4 w-4"
                          />
                        ) : (
                          <ChevronDown
                            data-testid="sort-indicator"
                            className="h-4 w-4"
                          />
                        )
                      ) : (
                        <ChevronsUpDown className="h-4 w-4 text-gray-400" />
                      )}
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {sortedData.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-6 py-12 text-center text-gray-500"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            sortedData.map((row, rowIndex) => (
              <tr
                key={getRowKey(row, rowIndex)}
                onClick={() => onRowClick?.(row)}
                onKeyDown={(e) => handleRowKeyDown(e, row)}
                tabIndex={onRowClick ? 0 : undefined}
                className={cn(
                  onRowClick && 'cursor-pointer hover:bg-gray-50 focus:outline-none focus:bg-gray-100'
                )}
              >
                {columns.map((column) => (
                  <td
                    key={String(column.key)}
                    className={cn(
                      'px-6 py-4 whitespace-nowrap text-sm text-gray-900',
                      column.className
                    )}
                  >
                    {column.render
                      ? column.render(row[column.key], row)
                      : String(row[column.key] ?? '')}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
