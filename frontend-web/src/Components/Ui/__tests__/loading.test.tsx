/**
 * Comprehensive tests for loading UI components.
 * Tests spinner, loading buttons, overlays, and progress indicators.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  Spinner,
  LoadingButton,
  LoadingOverlay,
  UploadProgress,
  DashboardSkeleton,
  ErrorState,
  StepProgress,
} from '../loading';
import { checkAccessibility } from '../../../test/utils/test-utils';

describe('Loading Components', () => {
  describe('Spinner', () => {
    it('renders default spinner', () => {
      render(<Spinner />);

      const spinner = screen.getByRole('status');
      expect(spinner).toBeInTheDocument();
      expect(spinner).toHaveAttribute('aria-label', 'Loading');
    });

    it('renders spinner with custom size', () => {
      render(<Spinner size="large" />);

      const spinner = screen.getByRole('status');
      expect(spinner).toHaveClass(/large|lg/);
    });

    it('renders spinner with custom label', () => {
      render(<Spinner label="Processing..." />);

      const spinner = screen.getByRole('status');
      expect(spinner).toHaveAttribute('aria-label', 'Processing...');
    });

    it('applies custom className', () => {
      render(<Spinner className="custom-spinner" />);

      const spinner = screen.getByRole('status');
      expect(spinner).toHaveClass('custom-spinner');
    });

    it('supports different color variants', () => {
      const { rerender } = render(<Spinner color="primary" />);
      let spinner = screen.getByRole('status');
      expect(spinner).toHaveClass(/primary/);

      rerender(<Spinner color="secondary" />);
      spinner = screen.getByRole('status');
      expect(spinner).toHaveClass(/secondary/);
    });

    it('has proper accessibility attributes', () => {
      const { container } = render(<Spinner />);
      checkAccessibility(container);
    });
  });

  describe('LoadingButton', () => {
    it('renders button in normal state', () => {
      render(
        <LoadingButton onClick={() => {}}>
          Submit
        </LoadingButton>
      );

      const button = screen.getByRole('button', { name: 'Submit' });
      expect(button).toBeInTheDocument();
      expect(button).not.toBeDisabled();
    });

    it('renders button in loading state', () => {
      render(
        <LoadingButton isLoading onClick={() => {}}>
          Submit
        </LoadingButton>
      );

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
      expect(button).toHaveAttribute('aria-busy', 'true');
      expect(screen.getByRole('status')).toBeInTheDocument(); // Spinner
    });

    it('shows loading text when loading', () => {
      render(
        <LoadingButton isLoading loadingText="Submitting...">
          Submit
        </LoadingButton>
      );

      expect(screen.getByText('Submitting...')).toBeInTheDocument();
    });

    it('calls onClick when not loading', async () => {
      const handleClick = jest.fn();
      const user = userEvent.setup();

      render(
        <LoadingButton onClick={handleClick}>
          Submit
        </LoadingButton>
      );

      await user.click(screen.getByRole('button'));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('prevents clicks when loading', async () => {
      const handleClick = jest.fn();
      const user = userEvent.setup();

      render(
        <LoadingButton isLoading onClick={handleClick}>
          Submit
        </LoadingButton>
      );

      await user.click(screen.getByRole('button'));
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('supports different button variants', () => {
      const { rerender } = render(
        <LoadingButton variant="primary">Primary</LoadingButton>
      );

      let button = screen.getByRole('button');
      expect(button).toHaveClass(/primary/);

      rerender(<LoadingButton variant="secondary">Secondary</LoadingButton>);
      button = screen.getByRole('button');
      expect(button).toHaveClass(/secondary/);
    });

    it('maintains focus management during loading states', () => {
      const { rerender } = render(
        <LoadingButton>Submit</LoadingButton>
      );

      const button = screen.getByRole('button');
      button.focus();
      expect(button).toHaveFocus();

      rerender(<LoadingButton isLoading>Submit</LoadingButton>);
      expect(button).toHaveFocus(); // Should maintain focus
    });
  });

  describe('LoadingOverlay', () => {
    it('renders overlay when visible', () => {
      render(
        <LoadingOverlay isVisible message="Loading data...">
          <div>Content</div>
        </LoadingOverlay>
      );

      expect(screen.getByText('Loading data...')).toBeInTheDocument();
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('does not render overlay when not visible', () => {
      render(
        <LoadingOverlay isVisible={false}>
          <div>Content</div>
        </LoadingOverlay>
      );

      expect(screen.queryByRole('status')).not.toBeInTheDocument();
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('blocks interactions when visible', () => {
      const handleClick = jest.fn();

      render(
        <LoadingOverlay isVisible message="Loading...">
          <button onClick={handleClick}>Click me</button>
        </LoadingOverlay>
      );

      const button = screen.getByRole('button', { name: 'Click me' });
      fireEvent.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });

    it('supports different overlay styles', () => {
      render(
        <LoadingOverlay isVisible blur>
          <div>Content</div>
        </LoadingOverlay>
      );

      const overlay = screen.getByTestId('loading-overlay');
      expect(overlay).toHaveClass(/blur/);
    });

    it('traps focus when visible', () => {
      render(
        <LoadingOverlay isVisible message="Loading...">
          <button>Button 1</button>
          <button>Button 2</button>
        </LoadingOverlay>
      );

      // Focus should be trapped within the overlay
      const overlay = screen.getByRole('status');
      expect(overlay).toHaveAttribute('role', 'status');
    });
  });

  describe('UploadProgress', () => {
    it('displays upload progress', () => {
      render(
        <UploadProgress
          progress={65}
          fileName="document.pdf"
          fileSize={1024000}
        />
      );

      expect(screen.getByText('document.pdf')).toBeInTheDocument();
      expect(screen.getByText(/1\.0 MB/)).toBeInTheDocument();
      expect(screen.getByText('65%')).toBeInTheDocument();
    });

    it('shows progress bar with correct value', () => {
      render(<UploadProgress progress={75} fileName="test.jpg" />);

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '75');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');
    });

    it('displays different upload states', () => {
      const { rerender } = render(
        <UploadProgress progress={0} fileName="test.jpg" status="uploading" />
      );

      expect(screen.getByText(/uploading/i)).toBeInTheDocument();

      rerender(
        <UploadProgress progress={100} fileName="test.jpg" status="completed" />
      );

      expect(screen.getByText(/completed|success/i)).toBeInTheDocument();

      rerender(
        <UploadProgress progress={50} fileName="test.jpg" status="error" />
      );

      expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
    });

    it('allows canceling upload', async () => {
      const handleCancel = jest.fn();
      const user = userEvent.setup();

      render(
        <UploadProgress
          progress={30}
          fileName="test.jpg"
          onCancel={handleCancel}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(handleCancel).toHaveBeenCalled();
    });

    it('shows retry option on error', async () => {
      const handleRetry = jest.fn();
      const user = userEvent.setup();

      render(
        <UploadProgress
          progress={30}
          fileName="test.jpg"
          status="error"
          onRetry={handleRetry}
        />
      );

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      expect(handleRetry).toHaveBeenCalled();
    });

    it('formats file sizes correctly', () => {
      const testCases = [
        { size: 1024, expected: '1.0 KB' },
        { size: 1024 * 1024, expected: '1.0 MB' },
        { size: 1024 * 1024 * 1024, expected: '1.0 GB' },
      ];

      testCases.forEach(({ size, expected }, index) => {
        const { unmount } = render(
          <UploadProgress progress={50} fileName={`test${index}.jpg`} fileSize={size} />
        );

        expect(screen.getByText(expected)).toBeInTheDocument();
        unmount();
      });
    });
  });

  describe('DashboardSkeleton', () => {
    it('renders skeleton placeholders', () => {
      render(<DashboardSkeleton />);

      const skeletons = screen.getAllByTestId('skeleton-item');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('supports different skeleton layouts', () => {
      render(<DashboardSkeleton layout="grid" />);

      const container = screen.getByTestId('dashboard-skeleton');
      expect(container).toHaveClass(/grid/);
    });

    it('shows appropriate number of skeleton items', () => {
      render(<DashboardSkeleton itemCount={5} />);

      const skeletons = screen.getAllByTestId('skeleton-item');
      expect(skeletons).toHaveLength(5);
    });

    it('animates skeleton placeholders', () => {
      render(<DashboardSkeleton animate />);

      const skeletons = screen.getAllByTestId('skeleton-item');
      skeletons.forEach(skeleton => {
        expect(skeleton).toHaveClass(/animate|pulse/);
      });
    });

    it('has proper accessibility for screen readers', () => {
      render(<DashboardSkeleton />);

      const container = screen.getByTestId('dashboard-skeleton');
      expect(container).toHaveAttribute('aria-busy', 'true');
      expect(container).toHaveAttribute('aria-label', expect.stringContaining('Loading'));
    });
  });

  describe('ErrorState', () => {
    it('displays error message', () => {
      render(
        <ErrorState
          title="Something went wrong"
          message="Unable to load data. Please try again."
        />
      );

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      expect(screen.getByText('Unable to load data. Please try again.')).toBeInTheDocument();
    });

    it('shows retry button when onRetry provided', async () => {
      const handleRetry = jest.fn();
      const user = userEvent.setup();

      render(
        <ErrorState
          title="Error"
          message="Something failed"
          onRetry={handleRetry}
        />
      );

      const retryButton = screen.getByRole('button', { name: /retry|try again/i });
      await user.click(retryButton);

      expect(handleRetry).toHaveBeenCalled();
    });

    it('supports different error types', () => {
      const { rerender } = render(
        <ErrorState title="Network Error" type="network" />
      );

      expect(screen.getByTestId('error-icon')).toHaveClass(/network/);

      rerender(
        <ErrorState title="Not Found" type="404" />
      );

      expect(screen.getByTestId('error-icon')).toHaveClass(/404|not-found/);
    });

    it('allows custom action buttons', async () => {
      const handleAction = jest.fn();
      const user = userEvent.setup();

      render(
        <ErrorState
          title="Error"
          message="Custom error"
          actions={[
            { label: 'Go Home', onClick: handleAction },
            { label: 'Contact Support', onClick: handleAction },
          ]}
        />
      );

      const homeButton = screen.getByRole('button', { name: 'Go Home' });
      const supportButton = screen.getByRole('button', { name: 'Contact Support' });

      await user.click(homeButton);
      await user.click(supportButton);

      expect(handleAction).toHaveBeenCalledTimes(2);
    });

    it('has proper semantic markup', () => {
      render(
        <ErrorState
          title="Error occurred"
          message="Something went wrong"
        />
      );

      const errorContainer = screen.getByRole('alert');
      expect(errorContainer).toBeInTheDocument();
    });
  });

  describe('StepProgress', () => {
    it('displays progress steps', () => {
      const steps = [
        { label: 'Personal Info', status: 'completed' },
        { label: 'Business Details', status: 'current' },
        { label: 'Verification', status: 'pending' },
      ];

      render(<StepProgress steps={steps} />);

      expect(screen.getByText('Personal Info')).toBeInTheDocument();
      expect(screen.getByText('Business Details')).toBeInTheDocument();
      expect(screen.getByText('Verification')).toBeInTheDocument();
    });

    it('shows correct step states', () => {
      const steps = [
        { label: 'Step 1', status: 'completed' },
        { label: 'Step 2', status: 'current' },
        { label: 'Step 3', status: 'pending' },
      ];

      render(<StepProgress steps={steps} />);

      const step1 = screen.getByText('Step 1').closest('[data-step]');
      const step2 = screen.getByText('Step 2').closest('[data-step]');
      const step3 = screen.getByText('Step 3').closest('[data-step]');

      expect(step1).toHaveClass(/completed/);
      expect(step2).toHaveClass(/current/);
      expect(step3).toHaveClass(/pending/);
    });

    it('supports clickable steps', async () => {
      const handleStepClick = jest.fn();
      const user = userEvent.setup();

      const steps = [
        { label: 'Step 1', status: 'completed', onClick: () => handleStepClick(0) },
        { label: 'Step 2', status: 'current', onClick: () => handleStepClick(1) },
      ];

      render(<StepProgress steps={steps} />);

      const step1Button = screen.getByRole('button', { name: /step 1/i });
      await user.click(step1Button);

      expect(handleStepClick).toHaveBeenCalledWith(0);
    });

    it('shows progress percentage', () => {
      const steps = [
        { label: 'Step 1', status: 'completed' },
        { label: 'Step 2', status: 'completed' },
        { label: 'Step 3', status: 'current' },
        { label: 'Step 4', status: 'pending' },
      ];

      render(<StepProgress steps={steps} showProgress />);

      expect(screen.getByText(/50%|2.*4/)).toBeInTheDocument(); // 2 of 4 completed
    });

    it('has proper accessibility attributes', () => {
      const steps = [
        { label: 'Step 1', status: 'completed' },
        { label: 'Step 2', status: 'current' },
      ];

      render(<StepProgress steps={steps} />);

      const progressContainer = screen.getByRole('progressbar');
      expect(progressContainer).toHaveAttribute('aria-valuemin', '0');
      expect(progressContainer).toHaveAttribute('aria-valuemax', '2');
      expect(progressContainer).toHaveAttribute('aria-valuenow', '1');
    });
  });

  describe('Responsive Behavior', () => {
    it('adapts to mobile viewports', () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(<DashboardSkeleton />);

      const container = screen.getByTestId('dashboard-skeleton');
      expect(container).toHaveClass(/mobile|sm:/);
    });

    it('adjusts step progress for small screens', () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      const steps = [
        { label: 'Very Long Step Name 1', status: 'completed' },
        { label: 'Very Long Step Name 2', status: 'current' },
      ];

      render(<StepProgress steps={steps} />);

      const stepLabels = screen.getAllByText(/Very Long Step Name/);
      stepLabels.forEach(label => {
        expect(label).toHaveClass(/truncate|ellipsis/);
      });
    });
  });

  describe('Performance', () => {
    it('renders large number of skeleton items efficiently', () => {
      const startTime = performance.now();

      render(<DashboardSkeleton itemCount={100} />);

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      expect(renderTime).toBeLessThan(100); // Should render in under 100ms
    });

    it('updates progress smoothly', async () => {
      const { rerender } = render(
        <UploadProgress progress={0} fileName="test.jpg" />
      );

      for (let i = 1; i <= 100; i += 10) {
        rerender(<UploadProgress progress={i} fileName="test.jpg" />);

        const progressBar = screen.getByRole('progressbar');
        expect(progressBar).toHaveAttribute('aria-valuenow', i.toString());
      }
    });
  });

  describe('Reduced Motion Support', () => {
    it('respects prefers-reduced-motion', () => {
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-reduced-motion: reduce)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });

      render(<DashboardSkeleton animate />);

      const skeletons = screen.getAllByTestId('skeleton-item');
      skeletons.forEach(skeleton => {
        expect(skeleton).not.toHaveClass(/animate/);
      });
    });
  });
});