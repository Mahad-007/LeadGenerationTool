import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LoadingSpinner } from './LoadingSpinner'

describe('LoadingSpinner', () => {
  it('renders spinner', () => {
    render(<LoadingSpinner />)
    expect(document.querySelector('svg')).toBeInTheDocument()
  })

  it('shows message when provided', () => {
    render(<LoadingSpinner message="Loading data..." />)
    expect(screen.getByText('Loading data...')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(<LoadingSpinner className="custom-class" />)
    expect(container.firstChild).toHaveClass('custom-class')
  })
})
