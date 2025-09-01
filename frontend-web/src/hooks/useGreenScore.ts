/**
 * GreenScore Hook
 * Manages GreenScore data and operations
 */
import { useState, useEffect } from 'react';
import { ai, GreenScore, CarbonCreditsPortfolio } from '../lib/api';

export const useGreenScore = () => {
  const [greenScore, setGreenScore] = useState<GreenScore | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [portfolio, setPortfolio] = useState<CarbonCreditsPortfolio | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCurrentScore = async () => {
    try {
      setLoading(true);
      setError(null);
      const score = await ai.getCurrentGreenScore();
      setGreenScore(score);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch GreenScore');
      console.error('Error fetching GreenScore:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async (months: number = 12) => {
    try {
      setLoading(true);
      const historyData = await ai.getGreenScoreHistory(months);
      setHistory(historyData.scores || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch history');
      console.error('Error fetching history:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchPortfolio = async () => {
    try {
      setLoading(true);
      const portfolioData = await ai.getCarbonCreditsPortfolio();
      setPortfolio(portfolioData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch portfolio');
      console.error('Error fetching portfolio:', err);
    } finally {
      setLoading(false);
    }
  };

  const processEvidence = async (file: File, sector: string, evidenceType: string, description?: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await ai.processEvidence({
        file,
        sector,
        region: 'Kenya',
        evidence_type: evidenceType,
        description,
      });

      // Refresh data after processing
      await fetchCurrentScore();
      await fetchPortfolio();
      
      return result;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process evidence');
      console.error('Error processing evidence:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentScore();
    fetchPortfolio();
  }, []);

  return {
    greenScore,
    history,
    portfolio,
    loading,
    error,
    fetchCurrentScore,
    fetchHistory,
    fetchPortfolio,
    processEvidence,
    refresh: () => {
      fetchCurrentScore();
      fetchHistory();
      fetchPortfolio();
    },
  };
};
