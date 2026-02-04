import { cn } from '@/lib/utils'
import { AlertCircle, X } from 'lucide-react'

export interface ErrorAlertProps {
  title?: string
  message: string
  onDismiss?: () => void
  className?: string
}

export function ErrorAlert({
  title = 'Error',
  message,
  onDismiss,
  className,
}: ErrorAlertProps) {
  return (
    <div
      role="alert"
      className={cn(
        'rounded-md bg-red-50 p-4 border border-red-200',
        className
      )}
    >
      <div className="flex">
        <div className="flex-shrink-0">
          <AlertCircle className="h-5 w-5 text-red-400" aria-hidden="true" />
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">{title}</h3>
          <p className="mt-1 text-sm text-red-700">{message}</p>
        </div>
        {onDismiss && (
          <div className="ml-auto pl-3">
            <button
              type="button"
              onClick={onDismiss}
              className="inline-flex rounded-md bg-red-50 p-1.5 text-red-500 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-600 focus:ring-offset-2"
            >
              <span className="sr-only">Dismiss</span>
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
