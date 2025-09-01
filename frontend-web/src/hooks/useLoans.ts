/**
 * Loans Hook
 * Manages loan applications and offers
 */
import { useState, useEffect } from 'react';
import { loans, LoanApplication } from '../lib/api';

export const useLoans = () => {
  const [userLoans, setUserLoans] = useState<LoanApplication[]>([]);
  const [loanOffers, setLoanOffers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUserLoans = async () => {
    try {
      setLoading(true);
      setError(null);
      const loansData = await loans.getUserLoans();
      setUserLoans(loansData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch loans');
      console.error('Error fetching loans:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchLoanOffers = async () => {
    try {
      setLoading(true);
      const offersData = await loans.getLoanOffers();
      setLoanOffers(offersData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch loan offers');
      console.error('Error fetching loan offers:', err);
    } finally {
      setLoading(false);
    }
  };

  const applyForLoan = async (amount: number, purpose: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await loans.applyForLoan({ amount, purpose });
      
      // Refresh loans after application
      await fetchUserLoans();
      await fetchLoanOffers();
      
      return result;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to apply for loan');
      console.error('Error applying for loan:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const acceptLoanOffer = async (loanId: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await loans.acceptLoanOffer(loanId);
      
      // Refresh data after acceptance
      await fetchUserLoans();
      await fetchLoanOffers();
      
      return result;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to accept loan offer');
      console.error('Error accepting loan offer:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserLoans();
    fetchLoanOffers();
  }, []);

  return {
    userLoans,
    loanOffers,
    loading,
    error,
    applyForLoan,
    acceptLoanOffer,
    refresh: () => {
      fetchUserLoans();
      fetchLoanOffers();
    },
  };
};
