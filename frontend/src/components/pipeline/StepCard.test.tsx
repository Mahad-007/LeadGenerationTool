import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StepCard, type StepCardProps } from './StepCard'
import type { StepState } from '@/types'

function renderStepCard(props: Partial<StepCardProps> = {}) {
  const defaultStepState: StepState = {
    status: 'idle',
    progress: 0,
    message: '',
  }

  const defaultProps: StepCardProps = {
    step: 'discovery',
    label: 'Site Discovery',
    stepNumber: 1,
    state: defaultStepState,
    isActive: false,
    ...props,
  }

  return render(<StepCard {...defaultProps} />)
}

describe('StepCard', () => {
  describe('rendering', () => {
    it('renders the step label', () => {
      renderStepCard({ label: 'Site Discovery' })
      expect(screen.getByText('Site Discovery')).toBeInTheDocument()
    })

    it('renders the step number', () => {
      renderStepCard({ stepNumber: 1 })
      expect(screen.getByText('Step 1')).toBeInTheDocument()
    })

    it('renders idle state by default', () => {
      renderStepCard()
      expect(screen.getByText(/waiting/i)).toBeInTheDocument()
    })
  })

  describe('status states', () => {
    it('shows running state with progress', () => {
      renderStepCard({
        state: {
          status: 'running',
          progress: 45,
          message: 'Processing sites...',
        },
      })
      expect(screen.getByText(/running/i)).toBeInTheDocument()
      expect(screen.getByText('45%')).toBeInTheDocument()
      expect(screen.getByText('Processing sites...')).toBeInTheDocument()
    })

    it('shows completed state', () => {
      renderStepCard({
        state: {
          status: 'completed',
          progress: 100,
          message: '',
          duration: 5000,
          itemsProcessed: 10,
        },
      })
      expect(screen.getByText(/completed/i)).toBeInTheDocument()
      expect(screen.getByText(/5s/)).toBeInTheDocument()
      expect(screen.getByText(/10 items/i)).toBeInTheDocument()
    })

    it('shows failed state with error', () => {
      renderStepCard({
        state: {
          status: 'failed',
          progress: 30,
          message: '',
          error: 'Connection timeout',
        },
      })
      expect(screen.getByText(/failed/i)).toBeInTheDocument()
      expect(screen.getByText('Connection timeout')).toBeInTheDocument()
    })

    it('shows pending state', () => {
      renderStepCard({
        state: {
          status: 'pending',
          progress: 0,
          message: '',
        },
      })
      expect(screen.getByText(/pending/i)).toBeInTheDocument()
    })
  })

  describe('active state', () => {
    it('highlights when active', () => {
      renderStepCard({ isActive: true })
      const card = screen.getByTestId('step-card')
      expect(card).toHaveClass('ring-2')
    })

    it('does not highlight when inactive', () => {
      renderStepCard({ isActive: false })
      const card = screen.getByTestId('step-card')
      expect(card).not.toHaveClass('ring-2')
    })
  })

  describe('progress bar', () => {
    it('shows progress bar when running', () => {
      renderStepCard({
        state: {
          status: 'running',
          progress: 50,
          message: '',
        },
      })
      expect(screen.getByRole('progressbar')).toBeInTheDocument()
    })

    it('hides progress bar when idle', () => {
      renderStepCard({
        state: {
          status: 'idle',
          progress: 0,
          message: '',
        },
      })
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has accessible region', () => {
      renderStepCard()
      expect(screen.getByRole('region')).toBeInTheDocument()
    })

    it('has aria-label with step name', () => {
      renderStepCard({ label: 'Site Discovery' })
      expect(screen.getByRole('region')).toHaveAttribute('aria-label', 'Site Discovery step')
    })
  })
})
