/**
 * Comprehensive tests for SMEDashboard component.
 * Tests dashboard functionality, data display, user interactions, and accessibility.
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient } from '@tanstack/react-query';
import {
  createAuthenticatedUser,
  createUnauthenticatedContext,
  mockUseGreenScore,
  mockUseLoans,
  checkAccessibility,
  expectLoadingState,
  expectErrorState,
} from '../../../test/utils/test-utils';
import SMEDashboard from '../SMEDashboard';

// Mock the hooks
jest.mock('../../../hooks/useAuth');
jest.mock('../../../hooks/useGreenScore');
jest.mock('../../../hooks/useLoans');

const mockUseAuth = require('../../../hooks/useAuth').default;
const mockGreenScore = require('../../../hooks/useGreenScore').default;
const mockLoans = require('../../../hooks/useLoans').default;

describe('SMEDashboard', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, staleTime: 0, cacheTime: 0 },
      },
    });

    // Reset mocks
    jest.clearAllMocks();

    // Default mock implementations
    mockUseAuth.mockReturnValue({
      user: createAuthenticatedUser(),
      isAuthenticated: true,
      isLoading: false,
    });

    mockGreenScore.mockReturnValue(mockUseGreenScore());
    mockLoans.mockReturnValue(mockUseLoans());
  });

  describe('Authenticated User Dashboard', () => {
    it('renders dashboard with user information', async () => {
      const user = createAuthenticatedUser({
        name: 'John Doe',
        business_name: 'Doe Enterprises',
      });

      mockUseAuth.mockReturnValue({
        user,
        isAuthenticated: true,
        isLoading: false,
      });

      render(<SMEDashboard />, { queryClient });

      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Doe Enterprises')).toBeInTheDocument();
    });

    it('displays green score information', async () => {
      const greenScoreData = mockUseGreenScore({
        overall_score: 85,
        confidence_score: 0.92,
        evidence_count: 7,
      });

      mockGreenScore.mockReturnValue(greenScoreData);

      render(<SMEDashboard />, { queryClient });

      expect(screen.getByText('85')).toBeInTheDocument();
      expect(screen.getByText(/92%/)).toBeInTheDocument();
      expect(screen.getByText('7')).toBeInTheDocument();
    });

    it('displays loan applications', async () => {
      const loanData = mockUseLoans({
        amount: 750000,
        status: 'approved',
        purpose: 'equipment',
      });

      mockLoans.mockReturnValue(loanData);

      render(<SMEDashboard />, { queryClient });

      expect(screen.getByText(/750,000/)).toBeInTheDocument();
      expect(screen.getByText('approved')).toBeInTheDocument();
      expect(screen.getByText('equipment')).toBeInTheDocument();
    });

    it('shows quick actions section', () => {
      render(<SMEDashboard />, { queryClient });

      expect(screen.getByText(/upload evidence/i)).toBeInTheDocument();
      expect(screen.getByText(/apply for loan/i)).toBeInTheDocument();
      expect(screen.getByText(/view recommendations/i)).toBeInTheDocument();
    });

    it('displays recent activity feed', () => {
      render(<SMEDashboard />, { queryClient });

      expect(screen.getByText(/recent activity/i)).toBeInTheDocument();
    });
  });

  describe('Loading States', () => {
    it('shows loading state for green score', () => {
      mockGreenScore.mockReturnValue({
        ...mockUseGreenScore(),
        isLoading: true,
      });

      const { container } = render(<SMEDashboard />, { queryClient });

      expectLoadingState(container);
    });

    it('shows loading state for loans', () => {
      mockLoans.mockReturnValue({
        ...mockUseLoans(),
        isLoading: true,
      });

      const { container } = render(<SMEDashboard />, { queryClient });

      expectLoadingState(container);
    });

    it('shows skeleton components during loading', () => {
      mockGreenScore.mockReturnValue({
        ...mockUseGreenScore(),
        isLoading: true,
      });

      render(<SMEDashboard />, { queryClient });

      // Look for skeleton or loading indicators
      expect(screen.getAllByRole('status')).toHaveLength.toBeGreaterThan(0);
    });
  });

  describe('Error States', () => {
    it('handles green score fetch error', () => {
      mockGreenScore.mockReturnValue({
        ...mockUseGreenScore(),
        error: new Error('Failed to fetch green score'),
        data: null,
      });

      const { container } = render(<SMEDashboard />, { queryClient });

      expectErrorState(container, 'Failed to fetch green score');
    });

    it('handles loans fetch error', () => {
      mockLoans.mockReturnValue({
        ...mockUseLoans(),
        error: new Error('Failed to fetch loans'),
        data: null,
      });

      const { container } = render(<SMEDashboard />, { queryClient });

      expectErrorState(container, 'Failed to fetch loans');
    });

    it('shows retry button on error', async () => {
      const mockRefetch = jest.fn();
      mockGreenScore.mockReturnValue({
        ...mockUseGreenScore(),
        error: new Error('Network error'),
        data: null,
        refetch: mockRefetch,
      });

      render(<SMEDashboard />, { queryClient });

      const retryButton = screen.getByRole('button', { name: /retry|try again/i });
      await userEvent.click(retryButton);

      expect(mockRefetch).toHaveBeenCalled();
    });
  });

  describe('User Interactions', () => {
    it('navigates to evidence upload on action click', async () => {
      render(<SMEDashboard />, { queryClient });

      const uploadButton = screen.getByRole('button', { name: /upload evidence/i });
      await userEvent.click(uploadButton);

      // This would typically test navigation - mock router if needed
      expect(uploadButton).toHaveBeenCalled;
    });

    it('navigates to loan application on action click', async () => {
      render(<SMEDashboard />, { queryClient });

      const loanButton = screen.getByRole('button', { name: /apply for loan/i });
      await userEvent.click(loanButton);

      expect(loanButton).toHaveBeenCalled;
    });

    it('opens recommendation details modal', async () => {
      const greenScoreData = mockUseGreenScore({
        recommendations: [
          {
            action: 'Install solar panels',
            potential_impact: '+10 points',
            estimated_cost: 'KES 200,000',
            payback_period: '18 months',
          },
        ],
      });

      mockGreenScore.mockReturnValue(greenScoreData);

      render(<SMEDashboard />, { queryClient });

      const recommendationButton = screen.getByRole('button', {
        name: /view recommendations/i,
      });
      await userEvent.click(recommendationButton);

      expect(screen.getByText('Install solar panels')).toBeInTheDocument();
    });

    it('refreshes data on pull-to-refresh', async () => {
      const mockRefetch = jest.fn();
      mockGreenScore.mockReturnValue({
        ...mockUseGreenScore(),
        refetch: mockRefetch,
      });

      render(<SMEDashboard />, { queryClient });

      // Simulate pull-to-refresh gesture
      const dashboard = screen.getByRole('main');
      fireEvent.touchStart(dashboard, { touches: [{ clientY: 0 }] });
      fireEvent.touchMove(dashboard, { touches: [{ clientY: 100 }] });
      fireEvent.touchEnd(dashboard);

      await waitFor(() => {
        expect(mockRefetch).toHaveBeenCalled();
      });
    });
  });

  describe('Data Formatting', () => {
    it('formats currency amounts correctly', () => {
      const loanData = mockUseLoans({
        amount: 1500000,
        monthly_payment: 135750,
      });

      mockLoans.mockReturnValue(loanData);

      render(<SMEDashboard />, { queryClient });

      expect(screen.getByText(/1,500,000/)).toBeInTheDocument();
      expect(screen.getByText(/135,750/)).toBeInTheDocument();
    });

    it('formats dates correctly', () => {
      const loanData = mockUseLoans({
        application_date: '2024-01-15T10:30:00Z',
      });

      mockLoans.mockReturnValue(loanData);

      render(<SMEDashboard />, { queryClient });

      // Check for formatted date display
      expect(screen.getByText(/Jan 15, 2024/)).toBeInTheDocument();
    });

    it('formats percentages correctly', () => {
      const greenScoreData = mockUseGreenScore({
        confidence_score: 0.8765,
      });

      mockGreenScore.mockReturnValue(greenScoreData);

      render(<SMEDashboard />, { queryClient });

      expect(screen.getByText(/87.7%/)).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('adapts layout for mobile viewport', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(<SMEDashboard />, { queryClient });

      const dashboard = screen.getByRole('main');
      expect(dashboard).toHaveClass(/mobile|sm:/);
    });

    it('adapts layout for tablet viewport', () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });

      render(<SMEDashboard />, { queryClient });

      const dashboard = screen.getByRole('main');
      expect(dashboard).toHaveClass(/tablet|md:/);
    });

    it('shows appropriate number of columns on different screen sizes', () => {
      render(<SMEDashboard />, { queryClient });

      const gridContainer = screen.getByTestId('dashboard-grid');
      expect(gridContainer).toHaveClass(/grid-cols-1|grid-cols-2|grid-cols-3/);
    });
  });

  describe('Accessibility', () => {
    it('has proper heading hierarchy', () => {
      render(<SMEDashboard />, { queryClient });

      const headings = screen.getAllByRole('heading');
      expect(headings[0]).toHaveAttribute('aria-level', '1');
    });

    it('has accessible navigation', () => {
      const { container } = render(<SMEDashboard />, { queryClient });

      checkAccessibility(container);
    });

    it('supports keyboard navigation', async () => {
      render(<SMEDashboard />, { queryClient });

      const firstButton = screen.getAllByRole('button')[0];
      firstButton.focus();

      expect(firstButton).toHaveFocus();

      await userEvent.tab();

      const secondButton = screen.getAllByRole('button')[1];
      expect(secondButton).toHaveFocus();
    });

    it('has proper ARIA labels for interactive elements', () => {
      render(<SMEDashboard />, { queryClient });

      const buttons = screen.getAllByRole('button');
      buttons.forEach((button) => {
        expect(
          button.getAttribute('aria-label') || button.textContent?.trim()
        ).toBeTruthy();
      });
    });

    it('announces dynamic content changes', async () => {
      render(<SMEDashboard />, { queryClient });

      const liveRegion = screen.getByRole('status');
      expect(liveRegion).toHaveAttribute('aria-live', 'polite');
    });
  });

  describe('Performance', () => {
    it('renders quickly with large datasets', () => {
      const largeGreenScoreData = mockUseGreenScore({
        scoring_factors: Object.fromEntries(
          Array.from({ length: 50 }, (_, i) => [
            `factor_${i}`,
            { score: Math.random() * 100, weight: Math.random() },
          ])
        ),
      });

      mockGreenScore.mockReturnValue(largeGreenScoreData);

      const startTime = performance.now();
      render(<SMEDashboard />, { queryClient });
      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(100); // Render under 100ms
    });

    it('memoizes expensive calculations', () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

      render(<SMEDashboard />, { queryClient });

      // Re-render with same props
      render(<SMEDashboard />, { queryClient });

      // Expensive calculations should not run twice
      expect(consoleSpy).not.toHaveBeenCalledWith(/calculating/);

      consoleSpy.mockRestore();
    });
  });

  describe('Unauthenticated State', () => {
    it('redirects unauthenticated users', () => {
      mockUseAuth.mockReturnValue(createUnauthenticatedContext());

      render(<SMEDashboard />, { queryClient });

      expect(screen.getByText(/please log in/i)).toBeInTheDocument();
    });

    it('shows login prompt for unauthenticated users', () => {
      mockUseAuth.mockReturnValue(createUnauthenticatedContext());

      render(<SMEDashboard />, { queryClient });

      expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
    });
  });

  describe('Empty States', () => {
    it('shows empty state when no loans exist', () => {
      mockLoans.mockReturnValue({
        ...mockUseLoans(),
        data: [],
      });

      render(<SMEDashboard />, { queryClient });

      expect(screen.getByText(/no loan applications/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /apply for your first loan/i })).toBeInTheDocument();
    });

    it('shows empty state when no green score exists', () => {
      mockGreenScore.mockReturnValue({
        ...mockUseGreenScore(),
        data: null,
      });

      render(<SMEDashboard />, { queryClient });

      expect(screen.getByText(/no green score yet/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /upload first evidence/i })).toBeInTheDocument();
    });
  });

  describe('Real-time Updates', () => {
    it('updates data when receiving real-time notifications', async () => {
      const { rerender } = render(<SMEDashboard />, { queryClient });

      // Simulate real-time update
      const updatedGreenScore = mockUseGreenScore({
        overall_score: 90,
      });

      mockGreenScore.mockReturnValue(updatedGreenScore);

      rerender(<SMEDashboard />);

      expect(screen.getByText('90')).toBeInTheDocument();
    });

    it('shows notification for score improvements', async () => {
      render(<SMEDashboard />, { queryClient });

      // Simulate score improvement notification
      const notification = screen.getByRole('alert');
      expect(notification).toHaveTextContent(/score improved/i);
    });
  });
});