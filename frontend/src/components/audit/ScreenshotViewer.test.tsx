import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ScreenshotViewer, type ScreenshotViewerProps } from './ScreenshotViewer'
import type { ViewportAudit } from '@/types'

const mockDesktopAudit: ViewportAudit = {
  viewport_type: 'desktop',
  viewport: { width: 1440, height: 900 },
  screenshot_path: '/screenshots/example-desktop.png',
  console_errors: [],
  performance_metrics: {
    lcp: 3624,
    fcp: 1936,
    dom_content_loaded: 2500,
    load_complete: 4200,
    ttfb: 350,
  },
  dom_info: {
    title: 'Example Store',
    h1: 'Welcome',
    ctas: [],
    ctasAboveFold: 2,
    ctasBelowFold: 3,
    heroInfo: {
      height: 600,
      hasImage: true,
    },
    brokenImages: [],
    internalLinksCount: 25,
    viewportHeight: 900,
    pageHeight: 2500,
    foldLine: 900,
  },
  link_issues: [],
  error: null,
}

const mockMobileAudit: ViewportAudit = {
  viewport_type: 'mobile',
  viewport: { width: 375, height: 812 },
  screenshot_path: '/screenshots/example-mobile.png',
  console_errors: [
    {
      type: 'error',
      text: 'Failed to load resource',
      location: {
        url: 'https://example.com/script.js',
        lineNumber: 10,
        columnNumber: 5,
      },
    },
  ],
  performance_metrics: {
    lcp: 4500,
    fcp: 2100,
    dom_content_loaded: 3000,
    load_complete: 5000,
    ttfb: 400,
  },
  dom_info: {
    title: 'Example Store',
    h1: 'Welcome',
    ctas: [],
    ctasAboveFold: 1,
    ctasBelowFold: 2,
    heroInfo: {
      height: 600,
      hasImage: true,
    },
    brokenImages: [],
    internalLinksCount: 20,
    viewportHeight: 812,
    pageHeight: 2000,
    foldLine: 812,
  },
  link_issues: [],
  error: null,
}

function renderScreenshotViewer(props: Partial<ScreenshotViewerProps> = {}) {
  const defaultProps: ScreenshotViewerProps = {
    url: 'https://example.com',
    desktop: mockDesktopAudit,
    mobile: mockMobileAudit,
    baseUrl: 'http://localhost:8000',
    ...props,
  }

  return render(<ScreenshotViewer {...defaultProps} />)
}

describe('ScreenshotViewer', () => {
  describe('rendering', () => {
    it('renders the site URL', () => {
      renderScreenshotViewer()
      expect(screen.getByText('example.com')).toBeInTheDocument()
    })

    it('renders desktop and mobile tabs', () => {
      renderScreenshotViewer()
      expect(screen.getByRole('tab', { name: /desktop/i })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /mobile/i })).toBeInTheDocument()
    })

    it('shows desktop tab as selected by default', () => {
      renderScreenshotViewer()
      const desktopTab = screen.getByRole('tab', { name: /desktop/i })
      expect(desktopTab).toHaveAttribute('aria-selected', 'true')
    })
  })

  describe('tab switching', () => {
    it('switches to mobile view when mobile tab is clicked', async () => {
      const user = userEvent.setup()
      renderScreenshotViewer()

      await user.click(screen.getByRole('tab', { name: /mobile/i }))

      const mobileTab = screen.getByRole('tab', { name: /mobile/i })
      expect(mobileTab).toHaveAttribute('aria-selected', 'true')
    })

    it('shows mobile viewport dimensions when mobile is selected', async () => {
      const user = userEvent.setup()
      renderScreenshotViewer()

      await user.click(screen.getByRole('tab', { name: /mobile/i }))

      expect(screen.getByText(/375 × 812/)).toBeInTheDocument()
    })

    it('shows desktop viewport dimensions by default', () => {
      renderScreenshotViewer()
      expect(screen.getByText(/1440 × 900/)).toBeInTheDocument()
    })
  })

  describe('screenshot display', () => {
    it('renders screenshot image with correct src', () => {
      renderScreenshotViewer()
      const img = screen.getByRole('img', { name: /desktop screenshot/i })
      expect(img).toHaveAttribute('src', 'http://localhost:8000/screenshots/example-desktop.png')
    })

    it('shows mobile screenshot when mobile tab is selected', async () => {
      const user = userEvent.setup()
      renderScreenshotViewer()

      await user.click(screen.getByRole('tab', { name: /mobile/i }))

      const img = screen.getByRole('img', { name: /mobile screenshot/i })
      expect(img).toHaveAttribute('src', 'http://localhost:8000/screenshots/example-mobile.png')
    })
  })

  describe('performance metrics', () => {
    it('displays LCP metric', () => {
      renderScreenshotViewer()
      expect(screen.getByText(/LCP/i)).toBeInTheDocument()
      expect(screen.getByText(/3624ms/)).toBeInTheDocument()
    })

    it('displays FCP metric', () => {
      renderScreenshotViewer()
      expect(screen.getByText(/FCP/i)).toBeInTheDocument()
      expect(screen.getByText(/1936ms/)).toBeInTheDocument()
    })

    it('displays TTFB metric', () => {
      renderScreenshotViewer()
      expect(screen.getByText(/TTFB/i)).toBeInTheDocument()
      expect(screen.getByText(/350ms/)).toBeInTheDocument()
    })
  })

  describe('console errors', () => {
    it('shows console errors count for mobile', async () => {
      const user = userEvent.setup()
      renderScreenshotViewer()

      await user.click(screen.getByRole('tab', { name: /mobile/i }))

      expect(screen.getByText(/1 error/i)).toBeInTheDocument()
    })

    it('shows no errors message for desktop', () => {
      renderScreenshotViewer()
      expect(screen.getByText(/no console errors/i)).toBeInTheDocument()
    })
  })

  describe('missing data handling', () => {
    it('handles missing desktop audit', () => {
      renderScreenshotViewer({ desktop: null })
      expect(screen.getByText(/no desktop screenshot/i)).toBeInTheDocument()
    })

    it('handles missing mobile audit', async () => {
      const user = userEvent.setup()
      renderScreenshotViewer({ mobile: null })

      await user.click(screen.getByRole('tab', { name: /mobile/i }))

      expect(screen.getByText(/no mobile screenshot/i)).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has accessible tablist', () => {
      renderScreenshotViewer()
      expect(screen.getByRole('tablist')).toBeInTheDocument()
    })

    it('has accessible tabpanel', () => {
      renderScreenshotViewer()
      expect(screen.getByRole('tabpanel')).toBeInTheDocument()
    })
  })
})
