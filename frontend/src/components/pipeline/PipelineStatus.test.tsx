import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PipelineStatus, type PipelineStatusProps } from './PipelineStatus'
import type { PipelineState } from '@/types'
import { createInitialPipelineState } from '@/types'

function renderPipelineStatus(props: Partial<PipelineStatusProps> = {}) {
  const defaultState: PipelineState = createInitialPipelineState()

  const defaultProps: PipelineStatusProps = {
    state: defaultState,
    overallProgress: 0,
    completedSteps: 0,
    totalSteps: 6,
    ...props,
  }

  return render(<PipelineStatus {...defaultProps} />)
}

describe('PipelineStatus', () => {
  describe('rendering', () => {
    it('renders the title', () => {
      renderPipelineStatus()
      expect(screen.getByText('Pipeline Status')).toBeInTheDocument()
    })

    it('shows idle status by default', () => {
      renderPipelineStatus()
      expect(screen.getByText(/idle/i)).toBeInTheDocument()
    })

    it('shows step count', () => {
      renderPipelineStatus({ completedSteps: 2, totalSteps: 6 })
      expect(screen.getByText(/2 \/ 6/i)).toBeInTheDocument()
    })
  })

  describe('status states', () => {
    it('shows running status with progress', () => {
      renderPipelineStatus({
        state: { ...createInitialPipelineState(), status: 'running' },
        overallProgress: 45,
        completedSteps: 2,
      })
      expect(screen.getByText(/running/i)).toBeInTheDocument()
      expect(screen.getByText('45%')).toBeInTheDocument()
    })

    it('shows completed status', () => {
      renderPipelineStatus({
        state: { ...createInitialPipelineState(), status: 'completed' },
        overallProgress: 100,
        completedSteps: 6,
      })
      // Use exact match to avoid matching "Steps Completed"
      expect(screen.getByText('Completed')).toBeInTheDocument()
    })

    it('shows failed status', () => {
      renderPipelineStatus({
        state: {
          ...createInitialPipelineState(),
          status: 'failed',
          error: 'Pipeline error occurred',
        },
      })
      expect(screen.getByText(/failed/i)).toBeInTheDocument()
      expect(screen.getByText('Pipeline error occurred')).toBeInTheDocument()
    })
  })

  describe('summary info', () => {
    it('shows summary when completed', () => {
      renderPipelineStatus({
        state: {
          ...createInitialPipelineState(),
          status: 'completed',
          summary: {
            totalDuration: 120000,
            stepsCompleted: 6,
            totalSteps: 6,
            sitesProcessed: 15,
          },
        },
        overallProgress: 100,
        completedSteps: 6,
      })
      expect(screen.getByText(/2m/)).toBeInTheDocument()
      expect(screen.getByText(/15 sites/i)).toBeInTheDocument()
    })
  })

  describe('progress bar', () => {
    it('shows progress bar when running', () => {
      renderPipelineStatus({
        state: { ...createInitialPipelineState(), status: 'running' },
        overallProgress: 50,
      })
      expect(screen.getByRole('progressbar')).toBeInTheDocument()
    })

    it('shows full progress bar when completed', () => {
      renderPipelineStatus({
        state: { ...createInitialPipelineState(), status: 'completed' },
        overallProgress: 100,
      })
      expect(screen.getByRole('progressbar')).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has accessible section', () => {
      renderPipelineStatus()
      expect(screen.getByRole('region')).toBeInTheDocument()
    })

    it('has aria-label', () => {
      renderPipelineStatus()
      expect(screen.getByRole('region')).toHaveAttribute('aria-label', 'Pipeline status')
    })
  })
})
