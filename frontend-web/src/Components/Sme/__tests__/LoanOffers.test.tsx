/**
 * Comprehensive tests for LoanOffers component.
 * Tests loan offer display, application process, and financial calculations.
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient } from '@tanstack/react-query';
import {
  createAuthenticatedUser,
  mockUseGreenScore,
  checkAccessibility,
  expectLoadingState,
  expectErrorState,
} from '../../../test/utils/test-utils';
import LoanOffers from '../LoanOffers';

// Mock the hooks and API
jest.mock('../../../hooks/useAuth');
jest.mock('../../../hooks/useGreenScore');
jest.mock('../../../lib/api');

const mockUseAuth = require('../../../hooks/useAuth').default;
const mockGreenScore = require('../../../hooks/useGreenScore').default;
const mockApi = require('../../../lib/api');

describe('LoanOffers', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, staleTime: 0, cacheTime: 0 },
      },
    });

    jest.clearAllMocks();

    // Default mock implementations
    mockUseAuth.mockReturnValue({
      user: createAuthenticatedUser(),
      isAuthenticated: true,
      isLoading: false,
    });

    mockGreenScore.mockReturnValue(mockUseGreenScore({
      overall_score: 75,
      confidence_score: 0.85,
    }));

    // Mock loan eligibility check
    mockApi.checkLoanEligibility = jest.fn().mockResolvedValue({
      eligible: true,
      max_amount: 1000000,
      min_amount: 50000,
      interest_rate: 12.5,
      max_term: 36,
      factors: ['green_score_bonus', 'verified_profile'],
    });

    // Mock loan application submission
    mockApi.applyForLoan = jest.fn().mockResolvedValue({
      application_id: '1',
      status: 'pending',
      message: 'Application submitted successfully',
    });
  });

  describe('Loan Offers Display', () => {
    it('renders available loan offers', async () => {
      render(<LoanOffers />, { queryClient });

      await waitFor(() => {
        expect(screen.getByText(/loan offers|available loans/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/equipment loan/i)).toBeInTheDocument();
      expect(screen.getByText(/working capital/i)).toBeInTheDocument();
      expect(screen.getByText(/expansion loan/i)).toBeInTheDocument();
    });

    it('displays loan terms and conditions', async () => {
      render(<LoanOffers />, { queryClient });

      await waitFor(() => {
        expect(screen.getByText(/12.5%/)).toBeInTheDocument(); // Interest rate
        expect(screen.getByText(/up to.*1,000,000/i)).toBeInTheDocument(); // Max amount
        expect(screen.getByText(/36.*months/i)).toBeInTheDocument(); // Max term
      });
    });

    it('shows green score impact on loan terms', async () => {
      mockGreenScore.mockReturnValue(mockUseGreenScore({
        overall_score: 85,
        confidence_score: 0.9,
      }));

      render(<LoanOffers />, { queryClient });

      await waitFor(() => {
        expect(screen.getByText(/green bonus|sustainability discount/i)).toBeInTheDocument();
        expect(screen.getByText(/reduced rate|lower interest/i)).toBeInTheDocument();
      });
    });

    it('displays personalized offers based on green score', async () => {
      const highScoreUser = mockUseGreenScore({
        overall_score: 90,
        confidence_score: 0.95,
      });

      mockGreenScore.mockReturnValue(highScoreUser);

      mockApi.checkLoanEligibility.mockResolvedValue({
        eligible: true,
        max_amount: 1500000,
        min_amount: 100000,
        interest_rate: 10.5,
        max_term: 48,
        factors: ['excellent_green_score', 'premium_borrower'],
      });

      render(<LoanOffers />, { queryClient });

      await waitFor(() => {
        expect(screen.getByText(/premium offer|excellent terms/i)).toBeInTheDocument();
        expect(screen.getByText(/10.5%/)).toBeInTheDocument();
        expect(screen.getByText(/1,500,000/)).toBeInTheDocument();
      });
    });
  });

  describe('Loan Calculator', () => {
    it('provides interactive loan calculator', async () => {
      const user = userEvent.setup();
      render(<LoanOffers />, { queryClient });

      await waitFor(() => {
        expect(screen.getByLabelText(/loan amount/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/repayment period|term/i)).toBeInTheDocument();
      });

      const amountInput = screen.getByLabelText(/loan amount/i);
      const termSelect = screen.getByLabelText(/repayment period|term/i);

      await user.clear(amountInput);
      await user.type(amountInput, '500000');
      await user.selectOptions(termSelect, '12');

      expect(screen.getByText(/monthly payment/i)).toBeInTheDocument();
      expect(screen.getByText(/44,471/)).toBeInTheDocument(); // Calculated payment
    });

    it('updates calculations in real-time', async () => {
      const user = userEvent.setup();
      render(<LoanOffers />, { queryClient });

      const amountInput = screen.getByLabelText(/loan amount/i);

      await user.clear(amountInput);
      await user.type(amountInput, '300000');

      await waitFor(() => {
        expect(screen.getByText(/26,683/)).toBeInTheDocument(); // Updated payment
      });
    });

    it('validates loan amount within limits', async () => {
      const user = userEvent.setup();
      render(<LoanOffers />, { queryClient });

      const amountInput = screen.getByLabelText(/loan amount/i);

      // Test amount too high
      await user.clear(amountInput);
      await user.type(amountInput, '2000000');

      expect(screen.getByText(/exceeds maximum|too high/i)).toBeInTheDocument();

      // Test amount too low
      await user.clear(amountInput);
      await user.type(amountInput, '10000');

      expect(screen.getByText(/below minimum|too low/i)).toBeInTheDocument();
    });

    it('shows total interest and repayment breakdown', async () => {
      const user = userEvent.setup();
      render(<LoanOffers />, { queryClient });

      const amountInput = screen.getByLabelText(/loan amount/i);
      await user.clear(amountInput);
      await user.type(amountInput, '500000');

      const viewBreakdownButton = screen.getByRole('button', { name: /view breakdown|details/i });
      await user.click(viewBreakdownButton);

      expect(screen.getByText(/total interest/i)).toBeInTheDocument();
      expect(screen.getByText(/total repayment/i)).toBeInTheDocument();
      expect(screen.getByText(/amortization schedule/i)).toBeInTheDocument();
    });
  });

  describe('Loan Application Process', () => {
    it('initiates loan application process', async () => {
      const user = userEvent.setup();
      render(<LoanOffers />, { queryClient });

      const applyButton = screen.getByRole('button', { name: /apply now|apply for loan/i });
      await user.click(applyButton);

      expect(screen.getByText(/loan application/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/loan purpose/i)).toBeInTheDocument();
    });

    it('collects required application information', async () => {
      const user = userEvent.setup();
      render(<LoanOffers />, { queryClient });

      const applyButton = screen.getByRole('button', { name: /apply now/i });
      await user.click(applyButton);

      expect(screen.getByLabelText(/loan amount/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/repayment term/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/loan purpose/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/business plan|use of funds/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/collateral/i)).toBeInTheDocument();
    });

    it('validates application form fields', async () => {
      const user = userEvent.setup();
      render(<LoanOffers />, { queryClient });

      const applyButton = screen.getByRole('button', { name: /apply now/i });
      await user.click(applyButton);

      const submitButton = screen.getByRole('button', { name: /submit application/i });
      await user.click(submitButton);

      expect(screen.getByText(/loan amount is required/i)).toBeInTheDocument();
      expect(screen.getByText(/purpose is required/i)).toBeInTheDocument();
    });

    it('submits loan application successfully', async () => {
      const user = userEvent.setup();
      render(<LoanOffers />, { queryClient });

      const applyButton = screen.getByRole('button', { name: /apply now/i });
      await user.click(applyButton);

      // Fill application form
      const amountInput = screen.getByLabelText(/loan amount/i);
      await user.type(amountInput, '500000');

      const termSelect = screen.getByLabelText(/repayment term/i);
      await user.selectOptions(termSelect, '12');

      const purposeSelect = screen.getByLabelText(/loan purpose/i);
      await user.selectOptions(purposeSelect, 'equipment');

      const businessPlanTextarea = screen.getByLabelText(/business plan|use of funds/i);
      await user.type(businessPlanTextarea, 'Purchase new farming equipment to increase productivity');

      const collateralTextarea = screen.getByLabelText(/collateral/i);
      await user.type(collateralTextarea, 'Farm equipment and land title');

      // Submit application
      const submitButton = screen.getByRole('button', { name: /submit application/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockApi.applyForLoan).toHaveBeenCalledWith({
          amount: 500000,
          term: 12,
          purpose: 'equipment',
          business_plan_summary: 'Purchase new farming equipment to increase productivity',
          collateral_description: 'Farm equipment and land title',
        });
      });

      expect(screen.getByText(/application submitted|successfully applied/i)).toBeInTheDocument();
    });

    it('handles application submission errors', async () => {
      const user = userEvent.setup();

      mockApi.applyForLoan.mockRejectedValue(
        new Error('Application failed - insufficient documentation')
      );

      render(<LoanOffers />, { queryClient });

      const applyButton = screen.getByRole('button', { name: /apply now/i });
      await user.click(applyButton);

      // Fill minimal form
      const amountInput = screen.getByLabelText(/loan amount/i);
      await user.type(amountInput, '500000');

      const purposeSelect = screen.getByLabelText(/loan purpose/i);
      await user.selectOptions(purposeSelect, 'equipment');

      const submitButton = screen.getByRole('button', { name: /submit application/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/application failed|error submitting/i)).toBeInTheDocument();
        expect(screen.getByText(/insufficient documentation/i)).toBeInTheDocument();
      });
    });
  });

  describe('Eligibility Checks', () => {
    it('shows ineligible state for low green score', async () => {
      mockGreenScore.mockReturnValue(mockUseGreenScore({
        overall_score: 30,
        confidence_score: 0.4,
      }));

      mockApi.checkLoanEligibility.mockResolvedValue({
        eligible: false,
        reasons: ['insufficient_green_score', 'low_confidence'],
        suggestions: ['Upload more sustainability evidence', 'Improve green practices'],
      });

      render(<LoanOffers />, { queryClient });

      await waitFor(() => {
        expect(screen.getByText(/not eligible|eligibility requirements/i)).toBeInTheDocument();
        expect(screen.getByText(/insufficient green score/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/upload more evidence/i)).toBeInTheDocument();
      expect(screen.getByText(/improve green practices/i)).toBeInTheDocument();
    });

    it('shows pending verification state', async () => {
      mockUseAuth.mockReturnValue({
        user: createAuthenticatedUser({ is_verified: false }),
        isAuthenticated: true,
        isLoading: false,
      });

      render(<LoanOffers />, { queryClient });

      await waitFor(() => {
        expect(screen.getByText(/verification pending|complete verification/i)).toBeInTheDocument();
      });

      const verifyButton = screen.getByRole('button', { name: /complete verification/i });
      expect(verifyButton).toBeInTheDocument();
    });

    it('provides eligibility improvement suggestions', async () => {
      mockApi.checkLoanEligibility.mockResolvedValue({
        eligible: false,
        reasons: ['new_user', 'no_credit_history'],
        suggestions: [
          'Complete business profile',
          'Upload financial documents',
          'Build transaction history',
        ],
      });

      render(<LoanOffers />, { queryClient });

      await waitFor(() => {
        expect(screen.getByText(/improve eligibility|increase chances/i)).toBeInTheDocument();
        expect(screen.getByText(/complete business profile/i)).toBeInTheDocument();
        expect(screen.getByText(/upload financial documents/i)).toBeInTheDocument();
      });
    });
  });

  describe('Loading and Error States', () => {
    it('shows loading state while fetching offers', () => {
      mockApi.checkLoanEligibility.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      );

      const { container } = render(<LoanOffers />, { queryClient });

      expectLoadingState(container);
      expect(screen.getByText(/loading loan offers/i)).toBeInTheDocument();
    });

    it('handles API errors gracefully', async () => {
      mockApi.checkLoanEligibility.mockRejectedValue(
        new Error('Service temporarily unavailable')
      );

      const { container } = render(<LoanOffers />, { queryClient });

      await waitFor(() => {
        expectErrorState(container, 'Service temporarily unavailable');
      });

      const retryButton = screen.getByRole('button', { name: /retry|try again/i });
      expect(retryButton).toBeInTheDocument();
    });

    it('allows retry after error', async () => {
      const user = userEvent.setup();

      mockApi.checkLoanEligibility
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          eligible: true,
          max_amount: 1000000,
          interest_rate: 12.5,
        });

      render(<LoanOffers />, { queryClient });

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText(/loan offers/i)).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Design', () => {
    it('adapts layout for mobile devices', () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(<LoanOffers />, { queryClient });

      const container = screen.getByTestId('loan-offers-container');
      expect(container).toHaveClass(/mobile|sm:/);
    });

    it('shows calculator in modal on mobile', async () => {
      const user = userEvent.setup();

      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(<LoanOffers />, { queryClient });

      const calculatorButton = screen.getByRole('button', { name: /calculator/i });
      await user.click(calculatorButton);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper form structure and labels', () => {
      const { container } = render(<LoanOffers />, { queryClient });

      checkAccessibility(container);
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<LoanOffers />, { queryClient });

      const firstButton = screen.getAllByRole('button')[0];
      firstButton.focus();
      expect(firstButton).toHaveFocus();

      await user.tab();
      const secondButton = screen.getAllByRole('button')[1];
      expect(secondButton).toHaveFocus();
    });

    it('provides screen reader announcements for calculations', async () => {
      const user = userEvent.setup();
      render(<LoanOffers />, { queryClient });

      const amountInput = screen.getByLabelText(/loan amount/i);
      await user.type(amountInput, '500000');

      const liveRegion = screen.getByRole('status');
      expect(liveRegion).toHaveTextContent(/monthly payment.*44,471/i);
    });

    it('has proper ARIA labels for loan terms', () => {
      render(<LoanOffers />, { queryClient });

      const interestRate = screen.getByText(/12.5%/);
      expect(interestRate).toHaveAttribute('aria-label', /interest rate 12.5 percent/i);

      const maxAmount = screen.getByText(/1,000,000/);
      expect(maxAmount).toHaveAttribute('aria-label', /maximum amount one million/i);
    });
  });

  describe('Financial Calculations', () => {
    it('calculates monthly payments correctly', async () => {
      const user = userEvent.setup();
      render(<LoanOffers />, { queryClient });

      const testCases = [
        { amount: '100000', term: '6', expectedPayment: '17,333' },
        { amount: '500000', term: '12', expectedPayment: '44,471' },
        { amount: '750000', term: '24', expectedPayment: '35,416' },
      ];

      for (const testCase of testCases) {
        const amountInput = screen.getByLabelText(/loan amount/i);
        const termSelect = screen.getByLabelText(/term/i);

        await user.clear(amountInput);
        await user.type(amountInput, testCase.amount);
        await user.selectOptions(termSelect, testCase.term);

        await waitFor(() => {
          expect(screen.getByText(testCase.expectedPayment)).toBeInTheDocument();
        });
      }
    });

    it('applies green score discount correctly', async () => {
      const user = userEvent.setup();

      // High green score should get discount
      mockGreenScore.mockReturnValue(mockUseGreenScore({
        overall_score: 85,
      }));

      mockApi.checkLoanEligibility.mockResolvedValue({
        eligible: true,
        interest_rate: 10.5, // Discounted rate
        factors: ['green_score_discount'],
      });

      render(<LoanOffers />, { queryClient });

      await waitFor(() => {
        expect(screen.getByText(/10.5%/)).toBeInTheDocument();
        expect(screen.getByText(/green discount|sustainability bonus/i)).toBeInTheDocument();
      });
    });
  });
});