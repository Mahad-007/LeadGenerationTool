import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusBadge } from './StatusBadge'

describe('StatusBadge', () => {
  describe('rendering', () => {
    it('renders with default variant', () => {
      render(<StatusBadge>Default</StatusBadge>)
      expect(screen.getByText('Default')).toBeInTheDocument()
    })

    it('renders with success variant', () => {
      render(<StatusBadge variant="success">Success</StatusBadge>)
      const badge = screen.getByText('Success')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveClass('bg-green-100')
    })

    it('renders with error variant', () => {
      render(<StatusBadge variant="error">Error</StatusBadge>)
      const badge = screen.getByText('Error')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveClass('bg-red-100')
    })

    it('renders with warning variant', () => {
      render(<StatusBadge variant="warning">Warning</StatusBadge>)
      const badge = screen.getByText('Warning')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveClass('bg-yellow-100')
    })

    it('renders with info variant', () => {
      render(<StatusBadge variant="info">Info</StatusBadge>)
      const badge = screen.getByText('Info')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveClass('bg-blue-100')
    })

    it('renders with pending variant', () => {
      render(<StatusBadge variant="pending">Pending</StatusBadge>)
      const badge = screen.getByText('Pending')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveClass('bg-gray-100')
    })
  })

  describe('sizes', () => {
    it('renders small size', () => {
      render(<StatusBadge size="sm">Small</StatusBadge>)
      const badge = screen.getByText('Small')
      expect(badge).toHaveClass('text-xs')
    })

    it('renders medium size (default)', () => {
      render(<StatusBadge size="md">Medium</StatusBadge>)
      const badge = screen.getByText('Medium')
      expect(badge).toHaveClass('text-sm')
    })

    it('renders large size', () => {
      render(<StatusBadge size="lg">Large</StatusBadge>)
      const badge = screen.getByText('Large')
      expect(badge).toHaveClass('text-base')
    })
  })

  describe('custom className', () => {
    it('accepts additional className', () => {
      render(<StatusBadge className="custom-class">Custom</StatusBadge>)
      const badge = screen.getByText('Custom')
      expect(badge).toHaveClass('custom-class')
    })
  })
})
