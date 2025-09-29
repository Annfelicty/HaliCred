/**
 * API Client for HaliCred Backend
 * Handles all HTTP requests to the FastAPI backend
 */
import axios from 'axios';
import type { AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config: any) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: any) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: any) => response,
  (error: any) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
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

export interface CarbonCreditsPortfolio {
  user_id: string;
  total_credits: {
    issued: number;
    pending: number;
    projected: number;
  };
  total_value_usd: {
    earned: number;
    pending: number;
    projected: number;
  };
  credits_by_standard: Record<string, { tonnes: number; value: number }>;
  recent_issuances: Array<{
    date: string;
    tonnes: number;
    standard: string;
    value_usd: number;
    project: string;
  }>;
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

// API Functions

// Authentication
const normalizeError = (error: unknown): never => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string }>;
    const message = axiosError.response?.data?.detail || axiosError.message || 'Request failed';
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
  processEvidence: async (evidenceData: EvidenceUpload) => {
    const formData = new FormData();
    formData.append('file', evidenceData.file);
    formData.append('sector', evidenceData.sector);
    formData.append('region', evidenceData.region);
    formData.append('evidence_type', evidenceData.evidence_type);
    if (evidenceData.description) {
      formData.append('description', evidenceData.description);
    }

    const response = await apiClient.post('/ai/evidence/process', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  getCurrentGreenScore: async (): Promise<GreenScore | null> => {
    const response = await apiClient.get('/ai/greenscore/current');
    return response.data;
  },

  getGreenScoreHistory: async (months: number = 12) => {
    const response = await apiClient.get(`/ai/greenscore/history?months=${months}`);
    return response.data;
  },

  getCarbonCreditsPortfolio: async (): Promise<CarbonCreditsPortfolio> => {
    const response = await apiClient.get('/ai/carbon-credits/portfolio');
    return response.data;
  },

  getSectorAnalytics: async (sector: string, region: string = 'Kenya') => {
    const response = await apiClient.get(`/ai/sector/analytics?sector=${sector}&region=${region}`);
    return response.data;
  },
};

// Loan Management
export const loans = {
  applyForLoan: async (loanData: { amount: number; tenor: number; purpose?: string }) => {
    try {
      const response = await apiClient.post('/loan/apply', loanData);
      return response.data;
    } catch (error) {
      throw normalizeError(error);
    }
  },

  getUserLoans: async (): Promise<LoanRecord[]> => {
    try {
      const response = await apiClient.get('/loan/my');
      return response.data;
    } catch (error) {
      throw normalizeError(error);
    }
  },

  getLoanOffers: async (payload: { amount: number; tenor: number }) => {
    try {
      const response = await apiClient.post('/loan/quote', payload);
      return response.data;
    } catch (error) {
      throw normalizeError(error);
    }
  },

  acceptLoanOffer: async (loanId: string) => {
    try {
      const response = await apiClient.post(`/admin/applications/${loanId}/decision`, { decision: 'approve' });
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
