import { cn } from '@/lib/utils'

export type ProgressSize = 'sm' | 'md' | 'lg'
export type ProgressVariant = 'default' | 'success' | 'error' | 'warning'

export interface ProgressBarProps {
  progress: number
  size?: ProgressSize
  variant?: ProgressVariant
  showLabel?: boolean
  label?: string
  className?: string
}

const sizeStyles: Record<ProgressSize, string> = {
  sm: 'h-1',
  md: 'h-2',
  lg: 'h-3',
}

const variantStyles: Record<ProgressVariant, string> = {
  default: 'bg-blue-600',
  success: 'bg-green-600',
  error: 'bg-red-600',
  warning: 'bg-yellow-600',
}

export function ProgressBar({
  progress,
  size = 'md',
  variant = 'default',
  showLabel = false,
  label,
  className,
}: ProgressBarProps) {
  // Clamp progress to 0-100
  const clampedProgress = Math.min(100, Math.max(0, progress))

  return (
    <div className={cn('w-full', className)}>
      {(showLabel || label) && (
        <div className="flex justify-between mb-1">
          <span className="text-sm font-medium text-gray-700">
            {label || `${clampedProgress}%`}
          </span>
        </div>
      )}
      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={clampedProgress}
        className={cn(
          'w-full bg-gray-200 rounded-full overflow-hidden',
          sizeStyles[size]
        )}
      >
        <div
          className={cn(
            'h-full rounded-full transition-all duration-300 ease-out',
            variantStyles[variant]
          )}
          style={{ width: `${clampedProgress}%` }}
        />
      </div>
    </div>
  )
}
