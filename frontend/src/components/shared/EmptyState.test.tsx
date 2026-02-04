import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { EmptyState } from './EmptyState'

describe('EmptyState', () => {
  it('renders default title and message', () => {
    render(<EmptyState />)
    expect(screen.getByText('No data')).toBeInTheDocument()
    expect(screen.getByText('No items to display')).toBeInTheDocument()
  })

  it('renders custom title and message', () => {
    render(<EmptyState title="No results" message="Try a different search" />)
    expect(screen.getByText('No results')).toBeInTheDocument()
    expect(screen.getByText('Try a different search')).toBeInTheDocument()
  })

  it('renders action when provided', () => {
    render(
      <EmptyState
        title="No items"
        message="Get started"
        action={<button>Add Item</button>}
      />
    )
    expect(screen.getByRole('button', { name: 'Add Item' })).toBeInTheDocument()
  })

  it('renders custom icon when provided', () => {
    render(
      <EmptyState
        title="No items"
        message="Message"
        icon={<span data-testid="custom-icon">Icon</span>}
      />
    )
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument()
  })
})
