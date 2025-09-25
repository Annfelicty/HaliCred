/**
 * Loans Hook
 * Manages loan applications and offers
 */
import { useCallback, useEffect, useState } from 'react';
import { loans, LoanRecord } from '../lib/api';

interface QuoteParams {
  amount: number;
  tenor: number;
}

const DEFAULT_QUOTE: QuoteParams = {
  amount: 50000,
  tenor: 12,
};

export const useLoans = () => {
  const [userLoans, setUserLoans] = useState<LoanRecord[]>([]);
  const [loanOffers, setLoanOffers] = useState<any[]>([]);
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
        const response = await loans.getLoanOffers({ amount: payload.amount, tenor: payload.tenor });
        const options = Array.isArray(response?.options) ? response.options : response ?? [];
        setLoanOffers(options);
        setQuoteParams(payload);
      } catch (err: any) {
        setError(err?.response?.data?.detail || 'Failed to fetch loan offers');
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
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to fetch loans');
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
      } catch (err: any) {
        setError(err?.response?.data?.detail || 'Failed to apply for loan');
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
      } catch (err: any) {
        setError(err?.response?.data?.detail || 'Failed to accept loan offer');
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

