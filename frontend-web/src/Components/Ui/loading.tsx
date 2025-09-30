/**
 * Loading Components for Enhanced UX
 * Provides various loading states and progress indicators
 */

import { cn } from "../../lib/utils"
import { cva, type VariantProps } from "class-variance-authority"
import { Progress } from "./progress"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./card"
import { Badge } from "./badge"
import { Skeleton } from "./skeleton"

// Spinner component with variants
const spinnerVariants = cva(
  "animate-spin rounded-full border-2 border-current border-t-transparent",
  {
    variants: {
      size: {
        sm: "h-4 w-4",
        default: "h-6 w-6",
        lg: "h-8 w-8",
        xl: "h-12 w-12",
      },
    },
    defaultVariants: {
      size: "default",
    },
  }
)

export interface SpinnerProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof spinnerVariants> {}

export function Spinner({ className, size, ...props }: SpinnerProps) {
  return (
    <div
      className={cn(spinnerVariants({ size }), className)}
      {...props}
    />
  )
}

// Loading button component
interface LoadingButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean
  children: React.ReactNode
  loadingText?: string
}

export function LoadingButton({
  loading = false,
  children,
  loadingText,
  disabled,
  className,
  ...props
}: LoadingButtonProps) {
  return (
    <button
      disabled={loading || disabled}
      className={cn(
        "inline-flex items-center justify-center gap-2 transition-opacity",
        loading && "opacity-70",
        className
      )}
      {...props}
    >
      {loading && <Spinner size="sm" />}
      {loading && loadingText ? loadingText : children}
    </button>
  )
}

// Loading overlay component
interface LoadingOverlayProps {
  isLoading: boolean
  message?: string
  children: React.ReactNode
}

export function LoadingOverlay({ isLoading, message, children }: LoadingOverlayProps) {
  return (
    <div className="relative">
      {children}
      {isLoading && (
        <div className="absolute inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="flex flex-col items-center gap-4">
            <Spinner size="lg" className="text-primary" />
            {message && (
              <p className="text-sm text-muted-foreground text-center max-w-xs">
                {message}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// Progress with steps component
interface Step {
  label: string
  status: 'pending' | 'active' | 'completed' | 'error'
}

interface StepProgressProps {
  steps: Step[]
  currentStep?: number
}

export function StepProgress({ steps, currentStep }: StepProgressProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => (
          <div key={index} className="flex flex-col items-center gap-2">
            <div
              className={cn(
                "h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors",
                {
                  "bg-muted text-muted-foreground": step.status === 'pending',
                  "bg-primary text-primary-foreground": step.status === 'active',
                  "bg-green-500 text-white": step.status === 'completed',
                  "bg-red-500 text-white": step.status === 'error',
                }
              )}
            >
              {step.status === 'completed' ? '✓' : index + 1}
            </div>
            <span className={cn(
              "text-xs text-center max-w-20",
              {
                "text-muted-foreground": step.status === 'pending',
                "text-foreground font-medium": step.status === 'active',
                "text-green-600": step.status === 'completed',
                "text-red-600": step.status === 'error',
              }
            )}>
              {step.label}
            </span>
          </div>
        ))}
      </div>
      <Progress
        value={((steps.filter(s => s.status === 'completed').length) / steps.length) * 100}
        className="h-2"
      />
    </div>
  )
}

// Upload progress component
interface UploadProgressProps {
  progress: number
  fileName?: string
  status: 'uploading' | 'processing' | 'completed' | 'error'
  message?: string
}

export function UploadProgress({ progress, fileName, status, message }: UploadProgressProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Spinner
                size="sm"
                className={cn(
                  status === 'completed' && "hidden",
                  status === 'error' && "hidden"
                )}
              />
              {status === 'completed' && <span className="text-green-500">✓</span>}
              {status === 'error' && <span className="text-red-500">✗</span>}
              <span className="text-sm font-medium">
                {fileName || "Processing..."}
              </span>
            </div>
            <Badge
              variant={status === 'error' ? "destructive" : status === 'completed' ? "default" : "secondary"}
            >
              {status === 'uploading' && 'Uploading'}
              {status === 'processing' && 'Processing'}
              {status === 'completed' && 'Complete'}
              {status === 'error' && 'Error'}
            </Badge>
          </div>

          <Progress value={progress} className="h-2" />

          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{Math.round(progress)}%</span>
            {message && <span>{message}</span>}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Page loading skeleton
export function PageLoadingSkeleton() {
  return (
    <div className="space-y-6 p-6">
      <div className="space-y-2">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-6 w-32" />
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-32 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

// Dashboard skeleton for specific components
export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-64" />
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[...Array(3)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="space-y-3">
                <Skeleton className="h-6 w-6 rounded-full" />
                <Skeleton className="h-8 w-16" />
                <Skeleton className="h-4 w-24" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="flex items-center space-x-4">
                  <Skeleton className="h-12 w-12 rounded-full" />
                  <div className="space-y-2 flex-1">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-24" />
                  </div>
                  <Skeleton className="h-8 w-16" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// Error state component
interface ErrorStateProps {
  title?: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
}

export function ErrorState({
  title = "Something went wrong",
  description = "We encountered an error while loading this content.",
  action
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center space-y-4">
      <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center">
        <span className="text-2xl text-red-500">⚠️</span>
      </div>
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">{title}</h3>
        <p className="text-muted-foreground max-w-md">{description}</p>
      </div>
      {action && (
        <LoadingButton onClick={action.onClick}>
          {action.label}
        </LoadingButton>
      )}
    </div>
  )
}

// Empty state component
interface EmptyStateProps {
  title?: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
  icon?: React.ReactNode
}

export function EmptyState({
  title = "No data found",
  description = "There's nothing to show here yet.",
  action,
  icon
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center space-y-4">
      <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
        {icon || <span className="text-2xl">📂</span>}
      </div>
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">{title}</h3>
        <p className="text-muted-foreground max-w-md">{description}</p>
      </div>
      {action && (
        <LoadingButton onClick={action.onClick}>
          {action.label}
        </LoadingButton>
      )}
    </div>
  )
}