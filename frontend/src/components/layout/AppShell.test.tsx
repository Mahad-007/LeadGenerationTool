import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AppShell, type AppShellProps } from './AppShell'

function renderAppShell(props: Partial<AppShellProps> = {}) {
  const defaultProps: AppShellProps = {
    pipelineStatus: 'idle',
    currentStep: null,
    stepStatuses: {
      discovery: 'pending',
      verification: 'pending',
      audit: 'pending',
      analysis: 'pending',
      contacts: 'pending',
      outreach: 'pending',
    },
    onRunPipeline: () => {},
    onStopPipeline: () => {},
    onNavigate: () => {},
    children: <div data-testid="child-content">Child Content</div>,
    ...props,
  }

  return render(<AppShell {...defaultProps} />)
}

describe('AppShell', () => {
  describe('rendering', () => {
    it('renders the header', () => {
      renderAppShell()
      expect(screen.getByText('Shopify UI Audit Tool')).toBeInTheDocument()
    })

    it('renders the sidebar', () => {
      renderAppShell()
      expect(screen.getByText('Pipeline Steps')).toBeInTheDocument()
    })

    it('renders children in main content area', () => {
      renderAppShell()
      expect(screen.getByTestId('child-content')).toBeInTheDocument()
    })

    it('has main landmark for content area', () => {
      renderAppShell()
      expect(screen.getByRole('main')).toBeInTheDocument()
    })
  })

  describe('layout structure', () => {
    it('contains header, sidebar, and main content', () => {
      renderAppShell()

      // Header (banner)
      expect(screen.getByRole('banner')).toBeInTheDocument()

      // Sidebar (navigation)
      expect(screen.getByRole('navigation')).toBeInTheDocument()

      // Main content
      expect(screen.getByRole('main')).toBeInTheDocument()
    })
  })

  describe('prop passing', () => {
    it('passes pipeline status to header', () => {
      renderAppShell({ pipelineStatus: 'running' })
      expect(screen.getByText('Running')).toBeInTheDocument()
    })

    it('passes step statuses to sidebar', () => {
      renderAppShell({
        stepStatuses: {
          discovery: 'completed',
          verification: 'running',
          audit: 'pending',
          analysis: 'pending',
          contacts: 'pending',
          outreach: 'pending',
        },
      })

      const discoveryButton = screen.getByRole('button', { name: /site discovery/i })
      expect(discoveryButton).toHaveAttribute('data-status', 'completed')
    })

    it('calls onRunPipeline from header', async () => {
      const onRunPipeline = vi.fn()
      renderAppShell({ onRunPipeline })

      const { userEvent } = await import('@testing-library/user-event')
      const user = userEvent.setup()

      await user.click(screen.getByRole('button', { name: /run pipeline/i }))
      expect(onRunPipeline).toHaveBeenCalled()
    })
  })
})
