import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Header, type HeaderProps } from './Header'

function renderHeader(props: Partial<HeaderProps> = {}) {
  const defaultProps: HeaderProps = {
    pipelineStatus: 'idle',
    onRunPipeline: () => {},
    onStopPipeline: () => {},
    ...props,
  }

  return render(<Header {...defaultProps} />)
}

describe('Header', () => {
  describe('rendering', () => {
    it('renders the app title', () => {
      renderHeader()
      expect(screen.getByText('Shopify UI Audit Tool')).toBeInTheDocument()
    })

    it('renders run pipeline button when idle', () => {
      renderHeader({ pipelineStatus: 'idle' })
      expect(screen.getByRole('button', { name: /run pipeline/i })).toBeInTheDocument()
    })

    it('renders stop pipeline button when running', () => {
      renderHeader({ pipelineStatus: 'running' })
      expect(screen.getByRole('button', { name: /stop pipeline/i })).toBeInTheDocument()
    })

    it('shows running indicator when pipeline is active', () => {
      renderHeader({ pipelineStatus: 'running' })
      expect(screen.getByText(/running/i)).toBeInTheDocument()
    })

    it('shows completed status', () => {
      renderHeader({ pipelineStatus: 'completed' })
      expect(screen.getByText(/completed/i)).toBeInTheDocument()
    })

    it('shows failed status', () => {
      renderHeader({ pipelineStatus: 'failed' })
      expect(screen.getByText(/failed/i)).toBeInTheDocument()
    })
  })

  describe('interactions', () => {
    it('calls onRunPipeline when run button is clicked', async () => {
      const user = userEvent.setup()
      const onRunPipeline = vi.fn()
      renderHeader({ pipelineStatus: 'idle', onRunPipeline })

      await user.click(screen.getByRole('button', { name: /run pipeline/i }))
      expect(onRunPipeline).toHaveBeenCalled()
    })

    it('calls onStopPipeline when stop button is clicked', async () => {
      const user = userEvent.setup()
      const onStopPipeline = vi.fn()
      renderHeader({ pipelineStatus: 'running', onStopPipeline })

      await user.click(screen.getByRole('button', { name: /stop pipeline/i }))
      expect(onStopPipeline).toHaveBeenCalled()
    })

    it('allows rerunning pipeline when completed', () => {
      renderHeader({ pipelineStatus: 'completed' })
      const runButton = screen.getByRole('button', { name: /run pipeline/i })
      expect(runButton).not.toBeDisabled()
    })
  })

  describe('accessibility', () => {
    it('has accessible banner landmark', () => {
      renderHeader()
      expect(screen.getByRole('banner')).toBeInTheDocument()
    })

    it('has heading for app title', () => {
      renderHeader()
      expect(screen.getByRole('heading', { name: /shopify ui audit tool/i })).toBeInTheDocument()
    })
  })
})
