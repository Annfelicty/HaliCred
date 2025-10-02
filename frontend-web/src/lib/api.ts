/**
 * API Client for HaliCred Backend
 * Handles all HTTP requests to the FastAPI backend
 */
import axios, { AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 90000, // 90 seconds for AI-powered endpoints
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      if (typeof config.headers?.set === 'function') {
        config.headers.set('Authorization', `Bearer ${token}`);
      } else {
        config.headers = {
          ...(config.headers ?? {}),
          Authorization: `Bearer ${token}`,
        } as InternalAxiosRequestConfig['headers'];
      }
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// Types
export interface User {
  id: string;
  phone: string;
  email?: string;
  full_name: string;
  roles: string[];
  created_at: string;
}

export interface OTPRequest {
  phone?: string;
  email?: string;
}

export interface VerifyOtpRequest extends OTPRequest {
  code: string;
  full_name?: string;
  password?: string;
  roles?: string[];
}

export interface PasswordLoginRequest {
  phone?: string;
  email?: string;
  password: string;
}

export interface BusinessProfile {
  business_type: string;
  business_name: string;
  location?: string;
  full_name?: string;
  phone?: string;
  email?: string;
}

export interface AuthSuccessResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  last_otp_verified_at?: string | null;
  last_login_at?: string | null;
}

export interface OTPResponse {
  status: string;
  message: string;
  expires_in: number;
}

export interface EvidenceUpload {
  file: File;
  sector: string;
  region: string;
  evidence_type: string;
  description?: string;
}

export interface GreenScore {
  user_id: string;
  greenscore: number;
  subscores: {
    energy_efficiency: number;
    renewable_energy: number;
    waste_management: number;
    water_conservation: number;
  };
  confidence: number;
  last_updated: string;
  sector_percentile: number;
  explainers: string[];
  actions: string[];
}

export interface ScoreHistoryEntry {
  date: string | number | Date;
  greenscore: number;
  change: number;
  evidence_count: number;
  co2_saved_tonnes: number;
}

export interface ScoreHistoryResponse {
  user_id: string;
  scores: ScoreHistoryEntry[];
  trend: string;
  improvement_suggestions: string[];
}

export interface AIProcessingResponse {
  request_id: string;
  status: string;
  message: string;
  processing_time_ms?: number;
  greenscore?: number;
  confidence?: number;
  carbon_credits?: unknown;
  review_required?: boolean;
}

export interface CarbonCreditSummary {
  count: number;
  tonnes_co2: number;
  value_usd: number;
}

export interface CarbonCreditIssuance {
  credit_id: string;
  evidence_id: string;
  standard: string;
  tonnes_co2: number;
  net_value_usd: number;
  issued_at: string | null;
}

export interface CarbonCreditRecord {
  id: string;
  evidence_id: string;
  greenscore_result_id: string;
  standard: string;
  status: string;
  approach: string;
  tonnes_co2: number;
  annual_tonnes: number;
  gross_value_usd: number;
  net_value_usd: number;
  estimated_issuance: string | null;
  actual_issuance: string | null;
  registry_id: string | null;
  created_at: string;
}

export interface CarbonCreditsPortfolio {
  user_id: string;
  summary: {
    issued: CarbonCreditSummary;
    pending: CarbonCreditSummary;
    eligible: CarbonCreditSummary;
    overall: CarbonCreditSummary;
  };
  recent_issuances: CarbonCreditIssuance[];
  credits: CarbonCreditRecord[];
}

export interface LoanRecord {
  id: string;
  amount: number;
  tenor: number;
  status: string;
  quoted_rate?: number | null;
  purpose?: string | null;
  created_at?: number | null;
  greenscore_snapshot?: Record<string, unknown> | null;
}

export interface LoanQuoteOption {
  tenor: number;
  rate: number;
  discount_reason?: string;
}

export interface LoanOffersResponse {
  options: LoanQuoteOption[];
}

// API Functions

// Authentication
const normalizeError = (error: unknown): never => {
  if (axios.isAxiosError(error)) {
    const payload = (error.response?.data as { detail?: string } | undefined)?.detail;
    const message = payload ?? error.message ?? 'Request failed';
    throw new Error(message);
  }
  if (error instanceof Error) {
    throw error;
  }
  throw new Error('Unknown error');
};

export const auth = {
  requestOtp: async (payload: OTPRequest): Promise<OTPResponse> => {
    try {
      const response = await apiClient.post('/auth/otp', payload);
      return response.data;
    } catch (error) {
      throw normalizeError(error);
    }
  },

  verifyOtp: async (payload: VerifyOtpRequest): Promise<AuthSuccessResponse> => {
    try {
      const response = await apiClient.post('/auth/verify', payload);
      return response.data;
    } catch (error) {
      throw normalizeError(error);
    }
  },

  loginWithPassword: async (payload: PasswordLoginRequest): Promise<AuthSuccessResponse> => {
    try {
      const response = await apiClient.post('/auth/login', payload);
      return response.data;
    } catch (error) {
      throw normalizeError(error);
    }
  },

  getCurrentUser: async (): Promise<User> => {
    try {
      const response = await apiClient.get('/me');
      return response.data;
    } catch (error) {
      throw normalizeError(error);
    }
  },
};

// Profile Management
export const profile = {
  updateProfile: async (profileData: Partial<BusinessProfile>) => {
    try {
      const response = await apiClient.patch('/me/profile', profileData);
      return response.data;
    } catch (error) {
      throw normalizeError(error);
    }
  },

  getProfile: async () => {
    try {
      const response = await apiClient.get('/me');
      return response.data;
    } catch (error) {
      throw normalizeError(error);
    }
  },
};

// AI Engine / Evidence Processing
export const ai = {
  processEvidence: async (evidenceData: EvidenceUpload): Promise<AIProcessingResponse> => {
    const formData = new FormData();
    formData.append('file', evidenceData.file);
    formData.append('sector', evidenceData.sector);
    formData.append('region', evidenceData.region);
    formData.append('evidence_type', evidenceData.evidence_type);
    if (evidenceData.description) {
      formData.append('description', evidenceData.description);
    }

    const response = await apiClient.post<AIProcessingResponse>('/ai/evidence/process', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  getCurrentGreenScore: async (): Promise<GreenScore | null> => {
    const response = await apiClient.get<GreenScore | null>('/ai/greenscore/current');
    return response.data;
  },

  getGreenScoreHistory: async (months: number = 12): Promise<ScoreHistoryResponse> => {
    const response = await apiClient.get<ScoreHistoryResponse>(`/ai/greenscore/history?months=${months}`);
    return response.data;
  },

  getCarbonCreditsPortfolio: async (): Promise<CarbonCreditsPortfolio> => {
    const response = await apiClient.get<CarbonCreditsPortfolio>('/ai/carbon-credits/portfolio');
    return response.data;
  },

  getSectorAnalytics: async (sector: string, region: string = 'Kenya') => {
    const response = await apiClient.get(`/ai/sector/analytics?sector=${sector}&region=${region}`);
    return response.data;
  },
};

// Loan Management
export const loans = {
  applyForLoan: async (loanData: { amount: number; tenor: number; purpose?: string }): Promise<LoanRecord> => {
    try {
      const response = await apiClient.post<LoanRecord>('/loan/apply', loanData);
      return response.data;
    } catch (error) {
      throw normalizeError(error);
    }
  },

  getUserLoans: async (): Promise<LoanRecord[]> => {
    try {
      const response = await apiClient.get<LoanRecord[]>('/loan/my');
      return response.data;
    } catch (error) {
      throw normalizeError(error);
    }
  },

  getLoanOffers: async (payload: { amount: number; tenor: number }): Promise<LoanOffersResponse> => {
    try {
      const response = await apiClient.post<LoanOffersResponse>('/loan/quote', payload);
      return response.data;
    } catch (error) {
      throw normalizeError(error);
    }
  },

  acceptLoanOffer: async (loanId: string): Promise<LoanRecord> => {
    try {
      const response = await apiClient.post<LoanRecord>(`/admin/applications/${loanId}/decision`, { decision: 'approve' });
      return response.data;
    } catch (error) {
      throw normalizeError(error);
    }
  },
};

// Admin/Bank Functions
export const admin = {
  getLoanApplications: async (status?: string) => {
    const params = status ? `?status=${status}` : '';
    const response = await apiClient.get(`/admin/loan-applications${params}`);
    return response.data;
  },

  reviewLoanApplication: async (loanId: string, decision: 'approve' | 'reject', notes?: string) => {
    const response = await apiClient.post(`/admin/loans/${loanId}/review`, {
      decision,
      notes
    });
    return response.data;
  },

  getReviewQueue: async () => {
    const response = await apiClient.get('/ai/review/queue');
    return response.data;
  },

  getUserAnalytics: async () => {
    const response = await apiClient.get('/admin/analytics/users');
    return response.data;
  },
};

export default apiClient;
