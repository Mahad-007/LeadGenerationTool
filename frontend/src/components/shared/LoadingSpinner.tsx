import { cn } from '@/lib/utils'
import { Loader2 } from 'lucide-react'

export type SpinnerSize = 'sm' | 'md' | 'lg'

export interface LoadingSpinnerProps {
  size?: SpinnerSize
  className?: string
  message?: string
}

const sizeStyles: Record<SpinnerSize, string> = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
}

export function LoadingSpinner({
  size = 'md',
  className,
  message,
}: LoadingSpinnerProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn('flex items-center justify-center gap-2', className)}
    >
      <Loader2
        className={cn('animate-spin text-gray-500', sizeStyles[size])}
        aria-hidden="true"
      />
      <span className={message ? 'text-sm text-gray-500' : 'sr-only'}>
        {message || 'Loading...'}
      </span>
    </div>
  )
}
