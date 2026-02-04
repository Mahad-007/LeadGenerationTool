import { useState } from 'react'
import { cn } from '@/lib/utils'
import type { ViewportAudit } from '@/types'

export interface ScreenshotViewerProps {
  url: string
  desktop: ViewportAudit | null
  mobile: ViewportAudit | null
  baseUrl: string
}

type ViewportTab = 'desktop' | 'mobile'

function formatMetric(value: number | null): string {
  if (value === null) return 'N/A'
  return `${value}ms`
}

function getMetricColor(metric: string, value: number | null): string {
  if (value === null) return 'text-gray-500'

  // LCP thresholds
  if (metric === 'lcp') {
    if (value <= 2500) return 'text-green-600'
    if (value <= 4000) return 'text-yellow-600'
    return 'text-red-600'
  }

  // FCP thresholds
  if (metric === 'fcp') {
    if (value <= 1800) return 'text-green-600'
    if (value <= 3000) return 'text-yellow-600'
    return 'text-red-600'
  }

  // TTFB thresholds
  if (metric === 'ttfb') {
    if (value <= 800) return 'text-green-600'
    if (value <= 1800) return 'text-yellow-600'
    return 'text-red-600'
  }

  return 'text-gray-700'
}

function extractDomain(url: string): string {
  try {
    return new URL(url).hostname
  } catch {
    return url
  }
}

export function ScreenshotViewer({
  url,
  desktop,
  mobile,
  baseUrl,
}: ScreenshotViewerProps) {
  const [activeTab, setActiveTab] = useState<ViewportTab>('desktop')

  const currentAudit = activeTab === 'desktop' ? desktop : mobile
  const screenshotUrl = currentAudit
    ? `${baseUrl}${currentAudit.screenshot_path}`
    : null

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-sm font-medium text-gray-900">{extractDomain(url)}</h3>
      </div>

      {/* Tabs */}
      <div
        role="tablist"
        aria-label="Viewport selection"
        className="flex border-b border-gray-200"
      >
        <button
          id="desktop-tab"
          role="tab"
          aria-selected={activeTab === 'desktop'}
          aria-controls="desktop-panel"
          onClick={() => setActiveTab('desktop')}
          className={cn(
            'flex-1 px-4 py-3 text-sm font-medium transition-colors',
            'focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500',
            activeTab === 'desktop'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
          )}
        >
          Desktop
        </button>
        <button
          id="mobile-tab"
          role="tab"
          aria-selected={activeTab === 'mobile'}
          aria-controls="mobile-panel"
          onClick={() => setActiveTab('mobile')}
          className={cn(
            'flex-1 px-4 py-3 text-sm font-medium transition-colors',
            'focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500',
            activeTab === 'mobile'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
          )}
        >
          Mobile
        </button>
      </div>

      {/* Tab Panel */}
      <div
        role="tabpanel"
        id={`${activeTab}-panel`}
        aria-labelledby={`${activeTab}-tab`}
        tabIndex={0}
        className="p-4"
      >
        {currentAudit ? (
          <div className="space-y-4">
            {/* Viewport Info */}
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>
                {currentAudit.viewport.width} × {currentAudit.viewport.height}
              </span>
              {currentAudit.console_errors.length > 0 ? (
                <span className="text-red-600">
                  {currentAudit.console_errors.length} error{currentAudit.console_errors.length !== 1 ? 's' : ''}
                </span>
              ) : (
                <span className="text-green-600">No console errors</span>
              )}
            </div>

            {/* Screenshot */}
            <div className="border border-gray-200 rounded-lg overflow-hidden bg-gray-100">
              {screenshotUrl && (
                <img
                  src={screenshotUrl}
                  alt={`${activeTab} screenshot of ${extractDomain(url)}`}
                  className="w-full h-auto"
                />
              )}
            </div>

            {/* Performance Metrics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 uppercase tracking-wider">LCP</p>
                <p className={cn(
                  'text-lg font-semibold',
                  getMetricColor('lcp', currentAudit.performance_metrics.lcp)
                )}>
                  {formatMetric(currentAudit.performance_metrics.lcp)}
                </p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 uppercase tracking-wider">FCP</p>
                <p className={cn(
                  'text-lg font-semibold',
                  getMetricColor('fcp', currentAudit.performance_metrics.fcp)
                )}>
                  {formatMetric(currentAudit.performance_metrics.fcp)}
                </p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500 uppercase tracking-wider">TTFB</p>
                <p className={cn(
                  'text-lg font-semibold',
                  getMetricColor('ttfb', currentAudit.performance_metrics.ttfb)
                )}>
                  {formatMetric(currentAudit.performance_metrics.ttfb)}
                </p>
              </div>
            </div>

            {/* Console Errors */}
            {currentAudit.console_errors.length > 0 && (
              <div className="border border-red-200 rounded-lg bg-red-50 p-3">
                <h4 className="text-sm font-medium text-red-800 mb-2">Console Errors</h4>
                <ul className="space-y-1">
                  {currentAudit.console_errors.map((error) => (
                    <li
                      key={`${error.text}-${error.location?.url || ''}-${error.location?.lineNumber || 0}`}
                      className="text-xs text-red-700 font-mono"
                    >
                      {error.text}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p>No {activeTab} screenshot available</p>
          </div>
        )}
      </div>
    </div>
  )
}
