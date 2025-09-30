/**
 * Accessibility Components and Utilities
 * Provides WCAG 2.1 AA compliant components and utilities
 */

import { cn } from "../../lib/utils"
import { forwardRef, useEffect, useState } from "react"

// Skip Link Component
interface SkipLinkProps {
  href: string;
  children: React.ReactNode;
}

export function SkipLink({ href, children }: SkipLinkProps) {
  return (
    <a
      href={href}
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded-md z-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
    >
      {children}
    </a>
  )
}

// Visually Hidden Component
interface VisuallyHiddenProps {
  children: React.ReactNode;
  asChild?: boolean;
}

export function VisuallyHidden({ children, asChild = false }: VisuallyHiddenProps) {
  const Component = asChild ? 'span' : 'span';

  return (
    <Component className="sr-only">
      {children}
    </Component>
  )
}

// Focus Trap Component
interface FocusTrapProps {
  children: React.ReactNode;
  active?: boolean;
  className?: string;
}

export const FocusTrap = forwardRef<HTMLDivElement, FocusTrapProps>(
  ({ children, active = true, className }, ref) => {
    const [container, setContainer] = useState<HTMLDivElement | null>(null);

    useEffect(() => {
      if (!active || !container) return;

      const focusableElements = container.querySelectorAll(
        'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select'
      );

      const firstElement = focusableElements[0] as HTMLElement;
      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

      const handleTabKey = (e: KeyboardEvent) => {
        if (e.key !== 'Tab') return;

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement?.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement?.focus();
          }
        }
      };

      container.addEventListener('keydown', handleTabKey);
      firstElement?.focus();

      return () => {
        container.removeEventListener('keydown', handleTabKey);
      };
    }, [active, container]);

    return (
      <div
        ref={(node) => {
          if (typeof ref === 'function') ref(node);
          else if (ref) ref.current = node;
          setContainer(node);
        }}
        className={cn(className)}
      >
        {children}
      </div>
    );
  }
);

FocusTrap.displayName = "FocusTrap";

// Live Region Component for screen readers
interface LiveRegionProps {
  children: React.ReactNode;
  priority?: 'polite' | 'assertive';
  atomic?: boolean;
}

export function LiveRegion({ children, priority = 'polite', atomic = false }: LiveRegionProps) {
  return (
    <div
      aria-live={priority}
      aria-atomic={atomic}
      className="sr-only"
    >
      {children}
    </div>
  )
}

// Accessible Icon Component
interface AccessibleIconProps {
  children: React.ReactNode;
  label: string;
  decorative?: boolean;
}

export function AccessibleIcon({ children, label, decorative = false }: AccessibleIconProps) {
  if (decorative) {
    return (
      <span aria-hidden="true">
        {children}
      </span>
    );
  }

  return (
    <span role="img" aria-label={label}>
      {children}
    </span>
  );
}

// High Contrast Mode Detection Hook
export function useHighContrastMode() {
  const [isHighContrast, setIsHighContrast] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-contrast: high)');
    setIsHighContrast(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setIsHighContrast(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return isHighContrast;
}

// Reduced Motion Detection Hook
export function useReducedMotion() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return prefersReducedMotion;
}

// Color Blind Friendly Utilities
export const colorBlindFriendlyColors = {
  success: 'bg-blue-600 text-white', // Instead of green
  warning: 'bg-orange-600 text-white',
  error: 'bg-red-600 text-white',
  info: 'bg-indigo-600 text-white',
  // Use patterns or icons in addition to colors
  successWithPattern: 'bg-blue-600 text-white border-l-4 border-blue-800',
  warningWithPattern: 'bg-orange-600 text-white border-l-4 border-orange-800',
  errorWithPattern: 'bg-red-600 text-white border-l-4 border-red-800',
};

// Keyboard Navigation Hook
export function useKeyboardNavigation(ref: React.RefObject<HTMLElement>) {
  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Arrow key navigation for lists/grids
      const focusableElements = element.querySelectorAll(
        '[tabindex="0"], button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled])'
      );

      const currentIndex = Array.from(focusableElements).indexOf(document.activeElement as Element);

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          const nextIndex = (currentIndex + 1) % focusableElements.length;
          (focusableElements[nextIndex] as HTMLElement)?.focus();
          break;
        case 'ArrowUp':
          e.preventDefault();
          const prevIndex = currentIndex === 0 ? focusableElements.length - 1 : currentIndex - 1;
          (focusableElements[prevIndex] as HTMLElement)?.focus();
          break;
        case 'Home':
          e.preventDefault();
          (focusableElements[0] as HTMLElement)?.focus();
          break;
        case 'End':
          e.preventDefault();
          (focusableElements[focusableElements.length - 1] as HTMLElement)?.focus();
          break;
      }
    };

    element.addEventListener('keydown', handleKeyDown);
    return () => element.removeEventListener('keydown', handleKeyDown);
  }, [ref]);
}

// Text Size Utilities
export const textSizeClasses = {
  small: 'text-sm',
  medium: 'text-base',
  large: 'text-lg',
  extraLarge: 'text-xl',
  accessible: 'text-base min-h-[44px] min-w-[44px]', // Meets WCAG touch target size
};

// Focus Visible Utility
export const focusVisibleClasses = 'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-white';

// Accessible Form Components
interface AccessibleLabelProps {
  htmlFor: string;
  children: React.ReactNode;
  required?: boolean;
  className?: string;
}

export function AccessibleLabel({ htmlFor, children, required = false, className }: AccessibleLabelProps) {
  return (
    <label
      htmlFor={htmlFor}
      className={cn('block text-sm font-medium text-gray-700 mb-1', className)}
    >
      {children}
      {required && (
        <span className="text-red-500 ml-1" aria-label="required">*</span>
      )}
    </label>
  );
}

interface AccessibleErrorMessageProps {
  id: string;
  children: React.ReactNode;
}

export function AccessibleErrorMessage({ id, children }: AccessibleErrorMessageProps) {
  return (
    <div
      id={id}
      role="alert"
      aria-live="assertive"
      className="mt-1 text-sm text-red-600"
    >
      {children}
    </div>
  );
}

// Accessible Button Component
interface AccessibleButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'small' | 'medium' | 'large';
  loading?: boolean;
  children: React.ReactNode;
}

export const AccessibleButton = forwardRef<HTMLButtonElement, AccessibleButtonProps>(
  ({ variant = 'primary', size = 'medium', loading = false, children, className, disabled, ...props }, ref) => {
    const baseClasses = cn(
      'inline-flex items-center justify-center rounded-md font-medium transition-colors',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      focusVisibleClasses,
      {
        'bg-blue-600 text-white hover:bg-blue-700': variant === 'primary',
        'bg-gray-600 text-white hover:bg-gray-700': variant === 'secondary',
        'bg-red-600 text-white hover:bg-red-700': variant === 'danger',
        'px-3 py-1.5 text-sm min-h-[32px]': size === 'small',
        'px-4 py-2 text-base min-h-[44px]': size === 'medium',
        'px-6 py-3 text-lg min-h-[48px]': size === 'large',
      },
      className
    );

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        aria-disabled={disabled || loading}
        className={baseClasses}
        {...props}
      >
        {loading && (
          <VisuallyHidden>Loading, please wait</VisuallyHidden>
        )}
        {children}
      </button>
    );
  }
);

AccessibleButton.displayName = "AccessibleButton";

// Progress Bar Component
interface AccessibleProgressProps {
  value: number;
  max?: number;
  label: string;
  showValue?: boolean;
}

export function AccessibleProgress({ value, max = 100, label, showValue = true }: AccessibleProgressProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        {showValue && (
          <span className="text-sm text-gray-500">{Math.round(percentage)}%</span>
        )}
      </div>
      <div
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-label={label}
        className="w-full bg-gray-200 rounded-full h-2"
      >
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

// Status Indicator Component
interface StatusIndicatorProps {
  status: 'success' | 'warning' | 'error' | 'info';
  children: React.ReactNode;
  showIcon?: boolean;
}

export function StatusIndicator({ status, children, showIcon = true }: StatusIndicatorProps) {
  const statusConfig = {
    success: {
      className: 'bg-green-50 border-green-200 text-green-800',
      icon: '✓',
      ariaLabel: 'Success'
    },
    warning: {
      className: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      icon: '⚠',
      ariaLabel: 'Warning'
    },
    error: {
      className: 'bg-red-50 border-red-200 text-red-800',
      icon: '✗',
      ariaLabel: 'Error'
    },
    info: {
      className: 'bg-blue-50 border-blue-200 text-blue-800',
      icon: 'ℹ',
      ariaLabel: 'Information'
    }
  };

  const config = statusConfig[status];

  return (
    <div
      role="status"
      aria-label={config.ariaLabel}
      className={cn('p-4 rounded-lg border', config.className)}
    >
      <div className="flex items-start space-x-3">
        {showIcon && (
          <AccessibleIcon label={config.ariaLabel} decorative>
            <span className="text-lg">{config.icon}</span>
          </AccessibleIcon>
        )}
        <div className="flex-1">
          {children}
        </div>
      </div>
    </div>
  );
}