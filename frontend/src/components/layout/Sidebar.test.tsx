import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Sidebar, type SidebarProps } from './Sidebar'
import type { PipelineStep } from '@/types'

function renderSidebar(props: Partial<SidebarProps> = {}) {
  const defaultProps: SidebarProps = {
    currentStep: null,
    stepStatuses: {
      discovery: 'pending',
      verification: 'pending',
      audit: 'pending',
      analysis: 'pending',
      contacts: 'pending',
      outreach: 'pending',
    },
    onNavigate: () => {},
    ...props,
  }

  return render(<Sidebar {...defaultProps} />)
}

describe('Sidebar', () => {
  describe('rendering', () => {
    it('renders the navigation title', () => {
      renderSidebar()
      expect(screen.getByText('Pipeline Steps')).toBeInTheDocument()
    })

    it('renders all six pipeline step buttons', () => {
      renderSidebar()
      expect(screen.getByRole('button', { name: /site discovery/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /shopify verification/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /homepage audit/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /ai analysis/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /contact extraction/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /email generation/i })).toBeInTheDocument()
    })

    it('displays step numbers', () => {
      renderSidebar()
      expect(screen.getByText('1')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
      expect(screen.getByText('4')).toBeInTheDocument()
      expect(screen.getByText('5')).toBeInTheDocument()
      expect(screen.getByText('6')).toBeInTheDocument()
    })
  })

  describe('step status indicators', () => {
    it('shows pending status by default', () => {
      renderSidebar()
      const discoveryButton = screen.getByRole('button', { name: /site discovery/i })
      expect(discoveryButton).toHaveAttribute('data-status', 'pending')
    })

    it('shows running status for current step', () => {
      renderSidebar({
        currentStep: 'discovery',
        stepStatuses: {
          discovery: 'running',
          verification: 'pending',
          audit: 'pending',
          analysis: 'pending',
          contacts: 'pending',
          outreach: 'pending',
        },
      })
      const discoveryButton = screen.getByRole('button', { name: /site discovery/i })
      expect(discoveryButton).toHaveAttribute('data-status', 'running')
    })

    it('shows completed status for finished steps', () => {
      renderSidebar({
        stepStatuses: {
          discovery: 'completed',
          verification: 'completed',
          audit: 'running',
          analysis: 'pending',
          contacts: 'pending',
          outreach: 'pending',
        },
      })
      const discoveryButton = screen.getByRole('button', { name: /site discovery/i })
      const verificationButton = screen.getByRole('button', { name: /shopify verification/i })
      expect(discoveryButton).toHaveAttribute('data-status', 'completed')
      expect(verificationButton).toHaveAttribute('data-status', 'completed')
    })

    it('shows failed status for errored steps', () => {
      renderSidebar({
        stepStatuses: {
          discovery: 'completed',
          verification: 'failed',
          audit: 'pending',
          analysis: 'pending',
          contacts: 'pending',
          outreach: 'pending',
        },
      })
      const verificationButton = screen.getByRole('button', { name: /shopify verification/i })
      expect(verificationButton).toHaveAttribute('data-status', 'failed')
    })
  })

  describe('navigation', () => {
    it('calls onNavigate when a step is clicked', async () => {
      const user = userEvent.setup()
      const onNavigate = vi.fn()
      renderSidebar({ onNavigate })

      await user.click(screen.getByRole('button', { name: /homepage audit/i }))
      expect(onNavigate).toHaveBeenCalledWith('audit')
    })

    it('highlights the current active step', () => {
      renderSidebar({ currentStep: 'audit' as PipelineStep })
      const auditButton = screen.getByRole('button', { name: /homepage audit/i })
      expect(auditButton).toHaveAttribute('aria-current', 'page')
    })
  })

  describe('accessibility', () => {
    it('has accessible navigation landmark', () => {
      renderSidebar()
      expect(screen.getByRole('navigation')).toBeInTheDocument()
    })

    it('has aria-label on navigation', () => {
      renderSidebar()
      expect(screen.getByRole('navigation')).toHaveAttribute('aria-label', 'Pipeline steps')
    })
  })
})
