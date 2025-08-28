import { useState } from 'react';
import { SMEOnboarding } from './sme/SMEOnboarding';
import { SMEDashboard } from './sme/SMEDashboard';
import { EvidenceUpload } from './sme/EvidenceUpload';
import { LoanOffers } from './sme/LoanOffers';
import { RepaymentTracker } from './sme/RepaymentTracker';

interface SMEAppProps {
  onBack: () => void;
}

export interface SMEUser {
  name: string;
  phone: string;
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
  loanApplications: Array<{
    id: string;
    amount: number;
    interestRate: number;
    term: number;
    status: 'pending' | 'approved' | 'disbursed' | 'active' | 'completed';
    purpose: string;
  }>;
}

export function SMEApp({ onBack }: SMEAppProps) {
  const [currentStep, setCurrentStep] = useState<'onboarding' | 'dashboard' | 'upload' | 'loans' | 'repayment'>('onboarding');
  const [user, setUser] = useState<SMEUser | null>(null);

  const handleCompleteOnboarding = (userData: Omit<SMEUser, 'greenScore' | 'ecoActions' | 'loanApplications'>) => {
    setUser({
      ...userData,
      greenScore: 45, // Starting score
      ecoActions: [],
      loanApplications: []
    });
    setCurrentStep('dashboard');
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

  const handleEvidenceUploaded = (evidence: any) => {
    if (user) {
      const newAction = {
        id: Date.now().toString(),
        type: evidence.type,
        description: evidence.description,
        date: new Date().toLocaleDateString(),
        verified: false,
        impact: evidence.impact
      };
      
      setUser({
        ...user,
        ecoActions: [...user.ecoActions, newAction],
        greenScore: Math.min(100, user.greenScore + Math.floor(Math.random() * 15) + 5)
      });
      
      setCurrentStep('dashboard');
    }
  };

  if (!user && currentStep !== 'onboarding') {
    return <SMEOnboarding onComplete={handleCompleteOnboarding} onBack={onBack} />;
  }

  switch (currentStep) {
    case 'onboarding':
      return <SMEOnboarding onComplete={handleCompleteOnboarding} onBack={onBack} />;
    
    case 'dashboard':
      return (
        <SMEDashboard 
          user={user!}
          onUploadEvidence={handleUploadEvidence}
          onViewLoans={handleViewLoans}
          onViewRepayments={handleViewRepayments}
          onBack={onBack}
        />
      );
    
    case 'upload':
      return (
        <EvidenceUpload 
          businessType={user!.businessType}
          onEvidenceUploaded={handleEvidenceUploaded}
          onBack={handleBackToDashboard}
        />
      );
    
    case 'loans':
      return (
        <LoanOffers 
          user={user!}
          onBack={handleBackToDashboard}
          onApplyForLoan={(loan) => {
            setUser({
              ...user!,
              loanApplications: [...user!.loanApplications, {
                id: Date.now().toString(),
                ...loan,
                status: 'pending'
              }]
            });
            setCurrentStep('dashboard');
          }}
        />
      );
    
    case 'repayment':
      return (
        <RepaymentTracker 
          user={user!}
          onBack={handleBackToDashboard}
        />
      );
    
    default:
      return null;
  }
}