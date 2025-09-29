/**
 * Loans Hook
 * Manages loan applications and offers
 */
import axios, { AxiosError } from 'axios';
import { useCallback, useEffect, useState } from 'react';
import { loans, LoanRecord, LoanOffersResponse, LoanQuoteOption } from '../lib/api';

interface QuoteParams {
  amount: number;
  tenor: number;
}

const DEFAULT_QUOTE: QuoteParams = {
  amount: 50000,
  tenor: 12,
};

const deriveErrorMessage = (error: unknown, fallback: string): string => {
  if (axios.isAxiosError(error)) {
    return (
      (error as AxiosError<{ detail?: string }>).response?.data?.detail ||
      error.message ||
      fallback
    );
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
};

export const useLoans = () => {
  const [userLoans, setUserLoans] = useState<LoanRecord[]>([]);
  const [loanOffers, setLoanOffers] = useState<LoanQuoteOption[]>([]);
  const [quoteParams, setQuoteParams] = useState<QuoteParams>(DEFAULT_QUOTE);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resolveQuoteParams = useCallback(
    (override?: Partial<QuoteParams>, fallbackLoans?: LoanRecord[]): QuoteParams => {
      const sourceLoans = fallbackLoans ?? userLoans;
      const referenceLoan = sourceLoans?.[0];

      const amount = override?.amount
        ?? (referenceLoan?.amount != null ? Number(referenceLoan.amount) : quoteParams.amount);

      const tenor = override?.tenor
        ?? (referenceLoan as LoanRecord & { tenor_months?: number })?.tenor
        ?? (referenceLoan as { tenor_months?: number })?.tenor_months
        ?? quoteParams.tenor;

      return {
        amount: Number.isFinite(amount) && amount > 0 ? amount : DEFAULT_QUOTE.amount,
        tenor: Number.isFinite(tenor) && tenor > 0 ? tenor : DEFAULT_QUOTE.tenor,
      };
    },
    [quoteParams.amount, quoteParams.tenor, userLoans]
  );

  const fetchLoanOffers = useCallback(
    async (override?: Partial<QuoteParams>, fallbackLoans?: LoanRecord[]) => {
      const payload = resolveQuoteParams(override, fallbackLoans);
      try {
        setLoading(true);
        setError(null);
        const response: LoanOffersResponse = await loans.getLoanOffers({ amount: payload.amount, tenor: payload.tenor });
        setLoanOffers(Array.isArray(response.options) ? response.options : []);
        setQuoteParams(payload);
      } catch (err) {
        const message = deriveErrorMessage(err, 'Failed to fetch loan offers');
        setError(message);
        console.error('Error fetching loan offers:', err);
      } finally {
        setLoading(false);
      }
    },
    [resolveQuoteParams]
  );

  const fetchUserLoans = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const loansData = await loans.getUserLoans();
      setUserLoans(loansData);
      await fetchLoanOffers(undefined, loansData);
    } catch (err) {
      const message = deriveErrorMessage(err, 'Failed to fetch loans');
      setError(message);
      console.error('Error fetching loans:', err);
    } finally {
      setLoading(false);
    }
  }, [fetchLoanOffers]);

  const applyForLoan = useCallback(
    async (amount: number, tenor: number, purpose: string) => {
      try {
        setLoading(true);
        setError(null);
        const result = await loans.applyForLoan({ amount, tenor, purpose });
        await fetchUserLoans();
        await fetchLoanOffers({ amount, tenor });
        return result;
      } catch (err) {
        const message = deriveErrorMessage(err, 'Failed to apply for loan');
        setError(message);
        console.error('Error applying for loan:', err);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [fetchLoanOffers, fetchUserLoans]
  );

  const acceptLoanOffer = useCallback(
    async (loanId: string) => {
      try {
        setLoading(true);
        setError(null);
        const result = await loans.acceptLoanOffer(loanId);
        await fetchUserLoans();
        await fetchLoanOffers();
        return result;
      } catch (err) {
        const message = deriveErrorMessage(err, 'Failed to accept loan offer');
        setError(message);
        console.error('Error accepting loan offer:', err);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [fetchLoanOffers, fetchUserLoans]
  );

  useEffect(() => {
    fetchUserLoans();
  }, [fetchUserLoans]);

  const refresh = useCallback(() => {
    fetchUserLoans();
  }, [fetchUserLoans]);

  return {
    userLoans,
    loanOffers,
    quoteParams,
    loading,
    error,
    applyForLoan,
    acceptLoanOffer,
    fetchLoanOffers,
    refresh,
  };
};

