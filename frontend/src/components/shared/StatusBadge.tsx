import { cn } from '@/lib/utils'

export type StatusVariant = 'default' | 'success' | 'error' | 'warning' | 'info' | 'pending'
export type StatusSize = 'sm' | 'md' | 'lg'

export interface StatusBadgeProps {
  children: React.ReactNode
  variant?: StatusVariant
  size?: StatusSize
  className?: string
}

const variantStyles: Record<StatusVariant, string> = {
  default: 'bg-gray-100 text-gray-800',
  success: 'bg-green-100 text-green-800',
  error: 'bg-red-100 text-red-800',
  warning: 'bg-yellow-100 text-yellow-800',
  info: 'bg-blue-100 text-blue-800',
  pending: 'bg-gray-100 text-gray-600',
}

const sizeStyles: Record<StatusSize, string> = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-0.5',
  lg: 'text-base px-3 py-1',
}

export function StatusBadge({
  children,
  variant = 'default',
  size = 'md',
  className,
}: StatusBadgeProps) {
  return (
    <span
      role="status"
      className={cn(
        'inline-flex items-center font-medium rounded-full',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
    >
      {children}
    </span>
  )
}
