import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { loans, profile, ai } from '../lib/api';
import type { LoanRecord } from '../lib/api';
import { SMEOnboarding } from './Sme/SMEOnboarding';
import { SMEDashboard } from './Sme/SMEDashboard';
import { EvidenceUpload, EvidenceUploadResult } from './Sme/EvidenceUpload';
import { LoanOffers } from './Sme/LoanOffers';
import { RepaymentTracker } from './Sme/RepaymentTracker';

const SME_PROFILE_STORAGE_KEY = 'sme_profile_cache';

type LoanStatusVariant = 'pending' | 'approved' | 'disbursed' | 'active' | 'completed';

export interface SMELoanApplication {
  id: string;
  amount: number;
  interestRate: number;
  term: number;
  tenor?: number;
  status: LoanStatusVariant;
  backendStatus: string;
  purpose: string;
  quotedRate?: number | null;
  createdAt?: number | null;
}

interface SMEAppProps {
  onBack: () => void;
}

export interface SMEUser {
  id: string;
  name: string;
  phone?: string;
  email?: string;
  businessType: 'farmer' | 'salon' | 'welding' | 'other';
  businessName: string;
  location: string;
  greenScore: number;
  ecoActions: Array<{
    id: string;
    type: string;
    description: string;
    date: string;
    verified: boolean;
    impact: string;
  }>;
  loanApplications: SMELoanApplication[];
}

const statusMap: Record<string, LoanStatusVariant> = {
  submitted: 'pending',
  pending: 'pending',
  approved: 'approved',
  disbursed: 'active',
  active: 'active',
  completed: 'completed',
  settled: 'completed',
};

const readStoredUser = (): SMEUser | null => {
  if (typeof window === 'undefined') {
    return null;
  }
  const raw = localStorage.getItem(SME_PROFILE_STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as SMEUser;
  } catch (error) {
    console.warn('Failed to parse stored SME profile', error);
    return null;
  }
};

const persistUser = (user: SMEUser) => {
  if (typeof window === 'undefined') {
    return;
  }
  try {
    localStorage.setItem(SME_PROFILE_STORAGE_KEY, JSON.stringify(user));
  } catch (error) {
    console.warn('Failed to persist SME profile', error);
  }
};

const toDisplayRate = (value: number | null | undefined, fallback?: number): number => {
  if (value != null) {
    const normalized = value <= 1 ? value * 100 : value;
    return Math.round(normalized * 100) / 100;
  }
  if (fallback != null) {
    return Math.round(fallback * 100) / 100;
  }
  return 16;
};

const transformLoanRecord = (record: LoanRecord, fallbackRate?: number): SMELoanApplication => {
  const status = statusMap[record.status] ?? 'pending';
  return {
    id: record.id,
    amount: record.amount,
    interestRate: toDisplayRate(record.quoted_rate, fallbackRate),
    term: record.tenor,
    tenor: record.tenor,
    status,
    backendStatus: record.status,
    purpose: record.purpose ?? 'General working capital',
    quotedRate: record.quoted_rate ?? null,
    createdAt: record.created_at ?? null,
  };
};

export function SMEApp({ onBack }: SMEAppProps) {
  const { isAuthenticated, loading: authLoading, user: identity } = useAuth();
  const [currentStep, setCurrentStep] = useState<'onboarding' | 'dashboard' | 'upload' | 'loans' | 'repayment'>('onboarding');
  const [user, setUser] = useState<SMEUser | null>(null);
  const [loadingUser, setLoadingUser] = useState(true);

  const fetchGreenScore = useCallback(async () => {
    try {
      const response = await ai.getCurrentGreenScore();

      if (response && typeof response.greenscore === 'number') {
        setUser((previous) => {
          if (!previous) {
            return previous;
          }
          const nextUser: SMEUser = {
            ...previous,
            greenScore: response.greenscore,
          };
          persistUser(nextUser);
          return nextUser;
        });
      }

      return response;
    } catch (error) {
      console.error('Failed to fetch GreenScore:', error);
      return null;
    }
  }, []);

  const loadUserData = useCallback(async () => {
    setLoadingUser(true);

    const cached = readStoredUser();

    if (!isAuthenticated) {
      if (cached) {
        setUser(cached);
        setCurrentStep('dashboard');
      } else {
        setUser(null);
        setCurrentStep('onboarding');
      }
      setLoadingUser(false);
      return;
    }

    try {
      const [profileResponse, loanResponse, greenscoreResponse] = await Promise.all([
        profile.getProfile(),
        loans.getUserLoans(),
        ai.getCurrentGreenScore().catch((error) => {
          console.error('Failed to fetch GreenScore during load:', error);
          return null;
        }),
      ]);

      const mappedLoans = Array.isArray(loanResponse)
        ? loanResponse.map((record) => transformLoanRecord(record))
        : [];

      const mergedUser: SMEUser = {
        id: profileResponse.id ?? cached?.id ?? identity?.id ?? '',
        name: profileResponse.full_name ?? cached?.name ?? identity?.full_name ?? '',
        phone: profileResponse.phone ?? cached?.phone ?? identity?.phone,
        email: profileResponse.email ?? cached?.email ?? identity?.email,
        businessType: cached?.businessType ?? 'other',
        businessName: cached?.businessName ?? '',
        location: cached?.location ?? '',
        greenScore:
          (greenscoreResponse && typeof greenscoreResponse?.greenscore === 'number'
            ? greenscoreResponse.greenscore
            : undefined) ?? cached?.greenScore ?? 0,
        ecoActions: cached?.ecoActions ?? [],
        loanApplications: mappedLoans,
      };

      setUser(mergedUser);
      persistUser(mergedUser);

      const hasProfileDetails = Boolean(mergedUser.businessName);
      setCurrentStep(hasProfileDetails ? 'dashboard' : 'onboarding');
    } catch (error) {
      console.error('Failed to load SME profile data:', error);
      if (cached) {
        setUser(cached);
        setCurrentStep('dashboard');
      } else {
        setUser(null);
        setCurrentStep('onboarding');
      }
    } finally {
      setLoadingUser(false);
    }
  }, [identity?.email, identity?.full_name, identity?.id, identity?.phone, isAuthenticated]);

  useEffect(() => {
    loadUserData();
  }, [loadUserData]);

  const handleCompleteOnboarding = async (userData: {
    name: string;
    phone: string;
    businessType: 'farmer' | 'salon' | 'welding' | 'other';
    businessName: string;
    location: string;
  }) => {
    try {
      // Save business profile to backend
      await profile.updateProfile({
        business_type: userData.businessType,
        business_name: userData.businessName,
        location: userData.location,
        full_name: userData.name,
        phone: userData.phone
      });

      // Create local user object for immediate UI update
      const composedUser: SMEUser = {
        id: user?.id || identity?.id || '',
        name: userData.name,
        phone: userData.phone,
        email: user?.email ?? identity?.email,
        businessType: userData.businessType,
        businessName: userData.businessName,
        location: userData.location,
        greenScore: user?.greenScore ?? 0,
        ecoActions: user?.ecoActions ?? [],
        loanApplications: user?.loanApplications ?? [],
      };

      setUser(composedUser);
      setCurrentStep('dashboard');
      persistUser(composedUser);
    } catch (error) {
      console.error('Failed to save business profile:', error);
      // Still proceed to dashboard with local data
      const composedUser: SMEUser = {
        id: user?.id || identity?.id || '',
        name: userData.name,
        phone: userData.phone,
        email: user?.email ?? identity?.email,
        businessType: userData.businessType,
        businessName: userData.businessName,
        location: userData.location,
        greenScore: user?.greenScore ?? 0,
        ecoActions: user?.ecoActions ?? [],
        loanApplications: user?.loanApplications ?? [],
      };

      setUser(composedUser);
      setCurrentStep('dashboard');
      persistUser(composedUser);
    }
  };

  const handleUploadEvidence = () => {
    setCurrentStep('upload');
  };

  const handleViewLoans = () => {
    setCurrentStep('loans');
  };

  const handleViewRepayments = () => {
    setCurrentStep('repayment');
  };

  const handleBackToDashboard = () => {
    setCurrentStep('dashboard');
  };

  const handleEvidenceUploaded = async (
    evidence: EvidenceUploadResult,
  ) => {
    setUser((previous) => {
      if (!previous) {
        return previous;
      }

      const verified = typeof evidence?.confidence === 'number' ? evidence.confidence >= 0.7 : false;
      const newAction = {
        id: Date.now().toString(),
        type: evidence.type,
        description: evidence.description,
        date: new Date().toLocaleDateString(),
        verified,
        impact: evidence.impact ?? 'Eco-impact calculated',
      };

      const nextUser: SMEUser = {
        ...previous,
        ecoActions: [...previous.ecoActions, newAction],
        greenScore:
          typeof evidence?.greenscore === 'number'
            ? evidence.greenscore
            : previous.greenScore,
      };

      persistUser(nextUser);
      return nextUser;
    });

    setCurrentStep('dashboard');

    await fetchGreenScore();
  };

  const handleApplyForLoan = async (payload: { amount: number; term: number; purpose: string; estimatedRate: number }) => {
    try {
      const response = await loans.applyForLoan({
        amount: payload.amount,
        tenor: payload.term,
        purpose: payload.purpose,
      });

      const newLoan = transformLoanRecord(response, payload.estimatedRate);

      setUser((previous) => {
        if (!previous) {
          return previous;
        }
        const nextUser: SMEUser = {
          ...previous,
          loanApplications: [newLoan, ...previous.loanApplications.filter((loan) => loan.id !== newLoan.id)],
        };
        persistUser(nextUser);
        return nextUser;
      });

      setCurrentStep('dashboard');
    } catch (error) {
      console.error('Loan application failed:', error);
      throw error;
    }
  };

  if (authLoading || loadingUser) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-50 via-green-50 to-teal-50">
        <div className="flex flex-col items-center space-y-3 text-green-700">
          <div className="w-10 h-10 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-medium">Loading your experience...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <SMEOnboarding onComplete={handleCompleteOnboarding} onBack={onBack} />;
  }

  switch (currentStep) {
    case 'onboarding':
      return <SMEOnboarding onComplete={handleCompleteOnboarding} onBack={onBack} />;

    case 'dashboard':
      return (
        <SMEDashboard
          user={user}
          onUploadEvidence={handleUploadEvidence}
          onViewLoans={handleViewLoans}
          onViewRepayments={handleViewRepayments}
          onBack={onBack}
        />
      );

    case 'upload':
      return (
        <EvidenceUpload
          businessType={user.businessType}
          onEvidenceUploaded={handleEvidenceUploaded}
          onBack={handleBackToDashboard}
        />
      );

    case 'loans':
      return (
        <LoanOffers
          user={user}
          onBack={handleBackToDashboard}
          onApplyForLoan={handleApplyForLoan}
        />
      );

    case 'repayment':
      return (
        <RepaymentTracker
          user={user}
          onBack={handleBackToDashboard}
        />
      );

    default:
      return null;
  }
}
