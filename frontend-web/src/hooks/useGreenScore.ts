/**
 * GreenScore Hook
 * Manages GreenScore data and operations
 */
import axios, { AxiosError } from 'axios';
import { useState, useEffect } from 'react';
import {
  ai,
  GreenScore,
  CarbonCreditsPortfolio,
  AIProcessingResponse,
  ScoreHistoryEntry,
  ScoreHistoryResponse,
} from '../lib/api';

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

export const useGreenScore = () => {
  const [greenScore, setGreenScore] = useState<GreenScore | null>(null);
  const [history, setHistory] = useState<ScoreHistoryEntry[]>([]);
  const [portfolio, setPortfolio] = useState<CarbonCreditsPortfolio | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCurrentScore = async () => {
    try {
      setLoading(true);
      setError(null);
      const score = await ai.getCurrentGreenScore();
      setGreenScore(score);
    } catch (err) {
      const message = deriveErrorMessage(err, 'Failed to fetch GreenScore');
      setError(message);
      console.error('Error fetching GreenScore:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async (months: number = 12) => {
    try {
      setLoading(true);
      const historyData: ScoreHistoryResponse = await ai.getGreenScoreHistory(months);
      setHistory(historyData.scores ?? []);
    } catch (err) {
      const message = deriveErrorMessage(err, 'Failed to fetch history');
      setError(message);
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
    } catch (err) {
      const message = deriveErrorMessage(err, 'Failed to fetch portfolio');
      setError(message);
      console.error('Error fetching portfolio:', err);
    } finally {
      setLoading(false);
    }
  };

  const processEvidence = async (
    file: File,
    sector: string,
    evidenceType: string,
    description?: string,
  ): Promise<AIProcessingResponse> => {
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

      await Promise.all([fetchCurrentScore(), fetchPortfolio()]);
      return result;
    } catch (err) {
      const message = deriveErrorMessage(err, 'Failed to process evidence');
      setError(message);
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

  const refresh = () => {
    fetchCurrentScore();
    fetchHistory();
    fetchPortfolio();
  };

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
    refresh,
  };
};
