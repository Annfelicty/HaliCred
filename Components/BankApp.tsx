import { useState } from 'react';
import { BankLogin } from './bank/BankLogin';
import { BankDashboard } from './bank/BankDashboard';
import { ApplicationQueue } from './bank/ApplicationQueue';
import { CaseReview } from './bank/CaseReview';
import { PortfolioDashboard } from './bank/PortfolioDashboard';

interface BankAppProps {
  onBack: () => void;
}

export interface LoanApplication {
  id: string;
  applicantName: string;
  businessName: string;
  businessType: 'farmer' | 'salon' | 'welding' | 'other';
  location: string;
  amount: number;
  purpose: string;
  greenScore: number;
  interestRate: number;
  term: number;
  status: 'pending' | 'under_review' | 'approved' | 'rejected' | 'disbursed';
  appliedDate: string;
  ecoActions: Array<{
    id: string;
    type: string;
    description: string;
    verified: boolean;
    evidence: string;
    ocrResult?: string;
    riskFlags?: string[];
  }>;
  riskAssessment: {
    creditScore: number;
    fraudRisk: 'low' | 'medium' | 'high';
    anomalies: string[];
    satelliteData?: {
      ndvi: number;
      landUse: string;
      verification: 'verified' | 'flagged';
    };
  };
}

export interface BankUser {
  name: string;
  role: 'underwriter' | 'manager' | 'admin';
  permissions: string[];
}

export function BankApp({ onBack }: BankAppProps) {
  const [currentView, setCurrentView] = useState<'login' | 'dashboard' | 'queue' | 'review' | 'portfolio'>('login');
  const [user, setUser] = useState<BankUser | null>(null);
  const [selectedApplication, setSelectedApplication] = useState<LoanApplication | null>(null);

  // Mock loan applications data
  const [applications] = useState<LoanApplication[]>([
    {
      id: 'APP001',
      applicantName: 'John Kiprotich',
      businessName: 'Kiprotich Dairy Farm',
      businessType: 'farmer',
      location: 'Eldoret, Kenya',
      amount: 150000,
      purpose: 'Solar water pump installation',
      greenScore: 78,
      interestRate: 14,
      term: 18,
      status: 'pending',
      appliedDate: '2024-01-15',
      ecoActions: [
        {
          id: '1',
          type: 'solar_pump',
          description: 'Solar water pump for irrigation',
          verified: false,
          evidence: 'receipt_solar_pump.jpg',
          ocrResult: 'SOLAR PUMP KES 89,000 - GREEN ENERGY SOLUTIONS LTD',
          riskFlags: []
        }
      ],
      riskAssessment: {
        creditScore: 725,
        fraudRisk: 'low',
        anomalies: [],
        satelliteData: {
          ndvi: 0.7,
          landUse: 'Agricultural',
          verification: 'verified'
        }
      }
    },
    {
      id: 'APP002',
      applicantName: 'Mary Wanjiku',
      businessName: 'Elegant Hair Salon',
      businessType: 'salon',
      location: 'Thika, Kenya',
      amount: 75000,
      purpose: 'Energy efficient equipment',
      greenScore: 65,
      interestRate: 15,
      term: 12,
      status: 'under_review',
      appliedDate: '2024-01-14',
      ecoActions: [
        {
          id: '2',
          type: 'led_lighting',
          description: 'LED lighting installation',
          verified: true,
          evidence: 'led_receipt.jpg',
          ocrResult: 'LED BULBS x12 KES 4,800 - PHILLIPS LIGHTING'
        }
      ],
      riskAssessment: {
        creditScore: 680,
        fraudRisk: 'low',
        anomalies: []
      }
    },
    {
      id: 'APP003',
      applicantName: 'Peter Otieno',
      businessName: 'Otieno Welding Works',
      businessType: 'welding',
      location: 'Kisumu, Kenya',
      amount: 200000,
      purpose: 'Inverter welding machine',
      greenScore: 72,
      interestRate: 14.5,
      term: 24,
      status: 'pending',
      appliedDate: '2024-01-13',
      ecoActions: [
        {
          id: '3',
          type: 'inverter_welder',
          description: 'Energy efficient inverter welder',
          verified: false,
          evidence: 'welder_receipt.jpg',
          riskFlags: ['High amount for business type']
        }
      ],
      riskAssessment: {
        creditScore: 701,
        fraudRisk: 'medium',
        anomalies: ['Amount above average for business type']
      }
    }
  ]);

  const handleLogin = (userData: BankUser) => {
    setUser(userData);
    setCurrentView('dashboard');
  };

  const handleViewQueue = () => {
    setCurrentView('queue');
  };

  const handleViewPortfolio = () => {
    setCurrentView('portfolio');
  };

  const handleReviewApplication = (application: LoanApplication) => {
    setSelectedApplication(application);
    setCurrentView('review');
  };

  const handleBackToDashboard = () => {
    setCurrentView('dashboard');
    setSelectedApplication(null);
  };

  const handleBackToQueue = () => {
    setCurrentView('queue');
    setSelectedApplication(null);
  };

  if (!user && currentView !== 'login') {
    return <BankLogin onLogin={handleLogin} onBack={onBack} />;
  }

  switch (currentView) {
    case 'login':
      return <BankLogin onLogin={handleLogin} onBack={onBack} />;
    
    case 'dashboard':
      return (
        <BankDashboard 
          user={user!}
          applications={applications}
          onViewQueue={handleViewQueue}
          onViewPortfolio={handleViewPortfolio}
          onBack={onBack}
        />
      );
    
    case 'queue':
      return (
        <ApplicationQueue 
          applications={applications}
          onReviewApplication={handleReviewApplication}
          onBack={handleBackToDashboard}
        />
      );
    
    case 'review':
      return (
        <CaseReview 
          application={selectedApplication!}
          onBack={handleBackToQueue}
          onDecision={(decision) => {
            // In real app, would update application status
            console.log('Decision:', decision);
            setCurrentView('queue');
          }}
        />
      );
    
    case 'portfolio':
      return (
        <PortfolioDashboard 
          applications={applications}
          onBack={handleBackToDashboard}
        />
      );
    
    default:
      return null;
  }
}