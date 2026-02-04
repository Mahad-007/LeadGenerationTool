import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ProgressBar } from './ProgressBar'

describe('ProgressBar', () => {
  describe('rendering', () => {
    it('renders with 0% progress', () => {
      render(<ProgressBar progress={0} />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toBeInTheDocument()
      expect(progressBar).toHaveAttribute('aria-valuenow', '0')
    })

    it('renders with 50% progress', () => {
      render(<ProgressBar progress={50} />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '50')
    })

    it('renders with 100% progress', () => {
      render(<ProgressBar progress={100} />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuenow', '100')
    })

    it('clamps progress to 0-100 range', () => {
      const { rerender } = render(<ProgressBar progress={150} />)
      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100')

      rerender(<ProgressBar progress={-10} />)
      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0')
    })
  })

  describe('label', () => {
    it('shows percentage label by default', () => {
      render(<ProgressBar progress={75} showLabel />)
      expect(screen.getByText('75%')).toBeInTheDocument()
    })

    it('hides label when showLabel is false', () => {
      render(<ProgressBar progress={75} showLabel={false} />)
      expect(screen.queryByText('75%')).not.toBeInTheDocument()
    })

    it('shows custom label when provided', () => {
      render(<ProgressBar progress={75} label="Processing..." />)
      expect(screen.getByText('Processing...')).toBeInTheDocument()
    })
  })

  describe('sizes', () => {
    it('renders small size', () => {
      render(<ProgressBar progress={50} size="sm" />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveClass('h-1')
    })

    it('renders medium size (default)', () => {
      render(<ProgressBar progress={50} size="md" />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveClass('h-2')
    })

    it('renders large size', () => {
      render(<ProgressBar progress={50} size="lg" />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveClass('h-3')
    })
  })

  describe('variants', () => {
    it('renders default variant', () => {
      render(<ProgressBar progress={50} />)
      const fill = screen.getByRole('progressbar').firstChild
      expect(fill).toHaveClass('bg-blue-600')
    })

    it('renders success variant', () => {
      render(<ProgressBar progress={50} variant="success" />)
      const fill = screen.getByRole('progressbar').firstChild
      expect(fill).toHaveClass('bg-green-600')
    })

    it('renders error variant', () => {
      render(<ProgressBar progress={50} variant="error" />)
      const fill = screen.getByRole('progressbar').firstChild
      expect(fill).toHaveClass('bg-red-600')
    })
  })

  describe('accessibility', () => {
    it('has correct ARIA attributes', () => {
      render(<ProgressBar progress={50} />)
      const progressBar = screen.getByRole('progressbar')
      expect(progressBar).toHaveAttribute('aria-valuemin', '0')
      expect(progressBar).toHaveAttribute('aria-valuemax', '100')
      expect(progressBar).toHaveAttribute('aria-valuenow', '50')
    })
  })
})
