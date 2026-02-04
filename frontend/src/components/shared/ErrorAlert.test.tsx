import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ErrorAlert } from './ErrorAlert'

describe('ErrorAlert', () => {
  it('renders error message', () => {
    render(<ErrorAlert message="Something went wrong" />)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('renders default title', () => {
    render(<ErrorAlert message="Error message" />)
    expect(screen.getByText('Error')).toBeInTheDocument()
  })

  it('renders custom title', () => {
    render(<ErrorAlert title="Custom Error" message="Error message" />)
    expect(screen.getByText('Custom Error')).toBeInTheDocument()
  })

  it('shows dismiss button when onDismiss is provided', () => {
    const onDismiss = vi.fn()
    render(<ErrorAlert message="Error" onDismiss={onDismiss} />)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('calls onDismiss when dismiss button is clicked', async () => {
    const user = userEvent.setup()
    const onDismiss = vi.fn()
    render(<ErrorAlert message="Error" onDismiss={onDismiss} />)

    await user.click(screen.getByRole('button'))
    expect(onDismiss).toHaveBeenCalled()
  })

  it('has alert role for accessibility', () => {
    render(<ErrorAlert message="Error" />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })
})
