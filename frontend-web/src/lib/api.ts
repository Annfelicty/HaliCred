/**
 * API Client for HaliCred Backend
 * Handles all HTTP requests to the FastAPI backend
 */
import axios from 'axios';

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
  full_name: string;
  roles: string[];
  created_at: string;
}

export interface LoginRequest {
  phone: string;
  password: string;
}

export interface RegisterRequest {
  phone: string;
  full_name: string;
  password: string;
  business_type?: string;
  business_name?: string;
}

export interface BusinessProfile {
  business_type: string;
  business_name: string;
  location?: {
    latitude: number;
    longitude: number;
  };
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

export interface LoanApplication {
  id: string;
  user_id: string;
  amount_requested: number;
  purpose: string;
  status: string;
  greenscore_at_application: number;
  created_at: string;
}

// API Functions

// Authentication
export const auth = {
  login: async (credentials: LoginRequest) => {
    const formData = new FormData();
    formData.append('username', credentials.phone);
    formData.append('password', credentials.password);
    
    const response = await apiClient.post('/auth/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    return response.data;
  },

  register: async (userData: RegisterRequest) => {
    const response = await apiClient.post('/auth/register', userData);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get('/profile/me');
    return response.data;
  },
};

// Profile Management
export const profile = {
  updateProfile: async (profileData: Partial<BusinessProfile>) => {
    const response = await apiClient.put('/profile/business', profileData);
    return response.data;
  },

  getProfile: async () => {
    const response = await apiClient.get('/profile/business');
    return response.data;
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
  applyForLoan: async (loanData: { amount: number; purpose: string }) => {
    const response = await apiClient.post('/loans/apply', loanData);
    return response.data;
  },

  getUserLoans: async () => {
    const response = await apiClient.get('/loans/my-loans');
    return response.data;
  },

  getLoanOffers: async () => {
    const response = await apiClient.get('/loans/offers');
    return response.data;
  },

  acceptLoanOffer: async (loanId: string) => {
    const response = await apiClient.post(`/loans/${loanId}/accept`);
    return response.data;
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
