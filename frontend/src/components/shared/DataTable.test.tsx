import { describe, it, expect, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { DataTable, type Column } from './DataTable'

interface TestData {
  id: number
  name: string
  status: string
  value: number
}

const testData: TestData[] = [
  { id: 1, name: 'Alpha', status: 'active', value: 100 },
  { id: 2, name: 'Beta', status: 'pending', value: 200 },
  { id: 3, name: 'Gamma', status: 'inactive', value: 300 },
]

const columns: Column<TestData>[] = [
  { key: 'name', header: 'Name' },
  { key: 'status', header: 'Status' },
  { key: 'value', header: 'Value' },
]

describe('DataTable', () => {
  describe('rendering', () => {
    it('renders table headers', () => {
      render(<DataTable data={testData} columns={columns} />)
      expect(screen.getByText('Name')).toBeInTheDocument()
      expect(screen.getByText('Status')).toBeInTheDocument()
      expect(screen.getByText('Value')).toBeInTheDocument()
    })

    it('renders table rows', () => {
      render(<DataTable data={testData} columns={columns} />)
      expect(screen.getByText('Alpha')).toBeInTheDocument()
      expect(screen.getByText('Beta')).toBeInTheDocument()
      expect(screen.getByText('Gamma')).toBeInTheDocument()
    })

    it('renders empty state when no data', () => {
      render(<DataTable data={[]} columns={columns} />)
      expect(screen.getByText('No data available')).toBeInTheDocument()
    })

    it('renders custom empty state', () => {
      render(
        <DataTable
          data={[]}
          columns={columns}
          emptyMessage="No items found"
        />
      )
      expect(screen.getByText('No items found')).toBeInTheDocument()
    })
  })

  describe('custom cell rendering', () => {
    it('supports custom render function', () => {
      const columnsWithRender: Column<TestData>[] = [
        { key: 'name', header: 'Name' },
        {
          key: 'status',
          header: 'Status',
          render: (value) => <span data-testid="custom-status">{String(value).toUpperCase()}</span>,
        },
      ]

      render(<DataTable data={testData} columns={columnsWithRender} />)
      const customStatuses = screen.getAllByTestId('custom-status')
      expect(customStatuses[0]).toHaveTextContent('ACTIVE')
    })
  })

  describe('sorting', () => {
    it('sorts by column when header is clicked', async () => {
      const user = userEvent.setup()
      const sortableColumns: Column<TestData>[] = [
        { key: 'name', header: 'Name', sortable: true },
        { key: 'value', header: 'Value', sortable: true },
      ]

      render(<DataTable data={testData} columns={sortableColumns} />)

      const rows = screen.getAllByRole('row')
      // First row is header, so data starts at index 1
      expect(within(rows[1]).getByText('Alpha')).toBeInTheDocument()

      // Click to sort by name descending
      await user.click(screen.getByText('Name'))
      const sortedRows = screen.getAllByRole('row')
      expect(within(sortedRows[1]).getByText('Gamma')).toBeInTheDocument()

      // Click again to sort ascending
      await user.click(screen.getByText('Name'))
      const ascendingRows = screen.getAllByRole('row')
      expect(within(ascendingRows[1]).getByText('Alpha')).toBeInTheDocument()
    })

    it('shows sort indicator on sorted column', async () => {
      const user = userEvent.setup()
      const sortableColumns: Column<TestData>[] = [
        { key: 'name', header: 'Name', sortable: true },
      ]

      render(<DataTable data={testData} columns={sortableColumns} />)

      await user.click(screen.getByText('Name'))
      expect(screen.getByTestId('sort-indicator')).toBeInTheDocument()
    })
  })

  describe('loading state', () => {
    it('shows loading state when loading prop is true', () => {
      render(<DataTable data={[]} columns={columns} loading />)
      expect(screen.getByTestId('table-loading')).toBeInTheDocument()
    })
  })

  describe('row click', () => {
    it('calls onRowClick when row is clicked', async () => {
      const user = userEvent.setup()
      const onRowClick = vi.fn()

      render(
        <DataTable data={testData} columns={columns} onRowClick={onRowClick} />
      )

      await user.click(screen.getByText('Alpha'))
      expect(onRowClick).toHaveBeenCalledWith(testData[0])
    })
  })
})
