import { useState } from 'react'
import { cn } from '@/lib/utils'
import type { PipelineConfig } from '@/types/pipeline'

export interface PipelineConfigModalProps {
  isOpen: boolean
  onClose: () => void
  onStart: (config: PipelineConfig) => void
}

export function PipelineConfigModal({
  isOpen,
  onClose,
  onStart,
}: PipelineConfigModalProps) {
  const [niche, setNiche] = useState('')
  const [maxSites, setMaxSites] = useState(10)
  const [error, setError] = useState('')

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!niche.trim()) {
      setError('Niche is required')
      return
    }

    setError('')
    onStart({
      niche: niche.trim(),
      maxSites,
    })

    // Reset form
    setNiche('')
    setMaxSites(10)
  }

  const handleClose = () => {
    setError('')
    setNiche('')
    setMaxSites(10)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Configure Pipeline
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Set the parameters for the pipeline run
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Niche Input */}
          <div>
            <label
              htmlFor="niche"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Niche <span className="text-red-500">*</span>
            </label>
            <input
              id="niche"
              type="text"
              value={niche}
              onChange={(e) => {
                setNiche(e.target.value)
                if (error) setError('')
              }}
              placeholder="e.g., fitness, fashion, home decor"
              className={cn(
                'w-full px-3 py-2 border rounded-md text-sm',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                error ? 'border-red-300' : 'border-gray-300'
              )}
            />
            {error && (
              <p className="mt-1 text-sm text-red-600">{error}</p>
            )}
          </div>

          {/* Max Sites Input */}
          <div>
            <label
              htmlFor="maxSites"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Max Sites
            </label>
            <input
              id="maxSites"
              type="number"
              min={1}
              max={100}
              value={maxSites}
              onChange={(e) => {
                const value = parseInt(e.target.value, 10)
                if (!isNaN(value)) {
                  setMaxSites(Math.min(100, Math.max(1, value)))
                }
              }}
              className={cn(
                'w-full px-3 py-2 border border-gray-300 rounded-md text-sm',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
              )}
            />
            <p className="mt-1 text-xs text-gray-500">
              Maximum number of sites to process (1-100)
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-md transition-colors',
                'bg-gray-100 text-gray-700 hover:bg-gray-200',
                'focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2'
              )}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-md transition-colors',
                'bg-blue-600 text-white hover:bg-blue-700',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
              )}
            >
              Start Pipeline
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
