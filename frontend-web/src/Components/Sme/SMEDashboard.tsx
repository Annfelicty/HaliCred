import { Button } from '../Ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../Ui/card';
import { Badge } from '../Ui/badge';
import { Progress } from '../Ui/progress';
import { SMEUser } from '../SMEApp';
import { useGreenScore } from '../../hooks/useGreenScore';
import { useEffect, useState } from 'react';
import { cn } from '../../lib/utils';
import { Spinner, LoadingOverlay, DashboardSkeleton, ErrorState, LoadingButton } from '../Ui/loading';
import {
  SkipLink,
  VisuallyHidden,
  AccessibleIcon,
  AccessibleProgress,
  useReducedMotion,
  focusVisibleClasses
} from '../Ui/accessibility';
import {
  Leaf,
  ArrowLeft,
  DollarSign,
  TrendingUp,
  Droplets,
  Zap,
  Recycle,
  User,
  Camera,
  CheckCircle,
  Clock,
  Sparkles,
  Star,
  Trophy,
  Target,
  Gift,
  Flame
} from 'lucide-react';

type LoanTone = 'pending' | 'approved' | 'active' | 'completed' | 'neutral';

interface LoanStatusInfo {
  label: string;
  helper?: string;
  tone: LoanTone;
}

const toneClasses: Record<LoanTone, { card: string; label: string; badge: string; helper: string }> = {
  pending: {
    card: 'border-yellow-200 bg-yellow-50',
    label: 'text-yellow-800',
    badge: 'bg-yellow-500/90 text-white',
    helper: 'bg-yellow-100 border-yellow-200 text-yellow-800',
  },
  approved: {
    card: 'border-emerald-200 bg-emerald-50',
    label: 'text-emerald-800',
    badge: 'bg-emerald-500/90 text-white',
    helper: 'bg-emerald-100 border-emerald-200 text-emerald-800',
  },
  active: {
    card: 'border-blue-200 bg-blue-50',
    label: 'text-blue-800',
    badge: 'bg-blue-500/90 text-white',
    helper: 'bg-blue-100 border-blue-200 text-blue-800',
  },
  completed: {
    card: 'border-green-200 bg-green-50',
    label: 'text-green-800',
    badge: 'bg-green-600 text-white',
    helper: 'bg-green-100 border-green-200 text-green-800',
  },
  neutral: {
    card: 'border-gray-200 bg-white',
    label: 'text-gray-800',
    badge: 'bg-gray-500/90 text-white',
    helper: 'bg-gray-100 border-gray-200 text-gray-700',
  },
};

const formatLabel = (value?: string | null) => {
  if (!value) {
    return 'Not specified';
  }

  return value
    .split(/[\s_-]+/)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ');
};

const resolveLoanStatus = (status: string | undefined): LoanStatusInfo => {
  switch (status) {
    case 'submitted':
    case 'pending':
      return {
        label: 'Application Pending',
        helper: "Your application is being reviewed. You'll be notified once a decision is made.",
        tone: 'pending',
      };
    case 'approved':
      return {
        label: 'Approved',
        helper: 'Awaiting disbursement to your account.',
        tone: 'approved',
      };
    case 'disbursed':
    case 'active':
      return {
        label: 'Active Loan',
        helper: 'Keep making timely repayments to unlock greener benefits.',
        tone: 'active',
      };
    case 'completed':
    case 'settled':
      return {
        label: 'Loan Completed',
        helper: 'Great work closing out your loan.',
        tone: 'completed',
      };
    default:
      return {
        label: 'Loan Status',
        tone: 'neutral',
      };
  }
};

const deriveDisplayRate = (quoted: number | null | undefined, fallback?: number) => {
  if (typeof quoted === 'number') {
    const normalized = quoted <= 1 ? quoted * 100 : quoted;
    return Math.round(normalized * 100) / 100;
  }

  if (typeof fallback === 'number') {
    return Math.round(fallback * 100) / 100;
  }

  return null;
};

interface SMEDashboardProps {
  user: SMEUser;
  onUploadEvidence: () => void;
  onViewLoans: () => void;
  onViewRepayments: () => void;
  onBack: () => void;
}

export function SMEDashboard({ user, onUploadEvidence, onViewLoans, onViewRepayments, onBack }: SMEDashboardProps) {
  const { greenScore, error: scoreError, fetchCurrentScore } = useGreenScore();

  // Static fallback recommendations shown immediately
  const staticRecommendations = [
    { action: 'Install energy-efficient LED lighting', priority: 'High', impact: 'Reduces energy costs by 40-60%' },
    { action: 'Implement solar water heating', priority: 'Medium', impact: 'Cuts water heating costs by 50-80%' },
    { action: 'Start composting organic waste', priority: 'Medium', impact: 'Reduces waste disposal costs and creates fertilizer' },
    { action: 'Switch to renewable energy sources', priority: 'High', impact: 'Long-term savings and carbon reduction' }
  ];

  const [recommendations, setRecommendations] = useState<any[]>(staticRecommendations);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [aiRecommendationsLoaded, setAiRecommendationsLoaded] = useState(false);
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        // Load score immediately
        await fetchCurrentScore();
        // Load AI recommendations in background (don't show loading spinner)
        fetchRecommendations(false);
      } finally {
        setInitialLoading(false);
      }
    };

    loadInitialData();
  }, []);

  const fetchRecommendations = async (showLoading: boolean = true) => {
    try {
      // Fetch AI-powered personalized recommendations from the API
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/ai/carbon-credits/recommendations`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
      });
      if (response.ok) {
        const data = await response.json();
        if (data.recommendations && data.recommendations.length > 0) {
          // When AI response arrives, show brief loading to indicate refresh is happening
          setLoadingRecommendations(true);
          await new Promise(resolve => setTimeout(resolve, 500)); // Brief loading animation to show update

          // Replace static recommendations with AI-powered ones
          setRecommendations(data.recommendations);
          setAiRecommendationsLoaded(true);
          setLoadingRecommendations(false);
        }
      }
    } catch (error) {
      console.error('Failed to fetch AI recommendations, using static fallback:', error);
      // Keep static recommendations if API fails
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Use real subscore data from API or fallback to user.greenScore-based values
  const ecoCategories = [
    {
      name: 'Energy',
      icon: Zap,
      score: greenScore?.subscores?.energy_efficiency || Math.max(0, user.greenScore - 10),
      color: 'text-yellow-600'
    },
    {
      name: 'Water',
      icon: Droplets,
      score: greenScore?.subscores?.water_conservation || Math.max(0, user.greenScore - 5),
      color: 'text-blue-600'
    },
    {
      name: 'Waste',
      icon: Recycle,
      score: greenScore?.subscores?.waste_management || Math.max(0, user.greenScore - 8),
      color: 'text-green-600'
    },
    {
      name: 'Renewable',
      icon: User,
      score: greenScore?.subscores?.renewable_energy || Math.max(0, user.greenScore - 12),
      color: 'text-purple-600'
    }
  ];

  // Use real AI recommendations or fallback to hardcoded tips
  const improvementTips = recommendations.length > 0
    ? recommendations.map(rec => ({
        action: rec.action,
        points: `+${Math.round(rec.estimated_co2_tonnes * 10)} pts`,
        description: `ROI: ${rec.payback_period_months} months`
      }))
    : [
        { action: 'Install LED lighting', points: '+15 pts', description: 'Replace incandescent bulbs' },
        { action: 'Solar water heating', points: '+20 pts', description: 'Reduce electricity usage' },
        { action: 'Waste separation', points: '+10 pts', description: 'Sort organic vs recyclable' },
        { action: 'Energy audit', points: '+12 pts', description: 'Professional assessment' }
      ];

  // Map backend status to frontend expected status
  const mapLoanStatus = (loan: any) => {
    if (!loan) return null;
    // Backend returns 'status', frontend expects 'backendStatus'
    const mappedLoan = { ...loan };
    mappedLoan.backendStatus = loan.status || loan.backendStatus;
    return mappedLoan;
  };

  const activeLoan = user.loanApplications.map(mapLoanStatus).find((loan) => loan?.backendStatus === 'active' || loan?.backendStatus === 'disbursed');
  const pendingLoan = user.loanApplications.map(mapLoanStatus).find((loan) => loan?.backendStatus === 'pending' || loan?.backendStatus === 'submitted');
  const fallbackLoan =
    user.loanApplications.map(mapLoanStatus).find((loan) => loan?.backendStatus === 'approved') ??
    user.loanApplications.map(mapLoanStatus).find((loan) => loan?.backendStatus === 'completed' || loan?.backendStatus === 'settled') ??
    user.loanApplications.map(mapLoanStatus)[0] ??
    null;

  const loanInFocus = activeLoan ?? pendingLoan ?? fallbackLoan;
  const loanStatusInfo = resolveLoanStatus(loanInFocus?.backendStatus);
  const tone = toneClasses[loanStatusInfo.tone];
  const StatusIcon =
    loanStatusInfo.tone === 'pending'
      ? Clock
      : loanStatusInfo.tone === 'neutral'
      ? DollarSign
      : CheckCircle;
  const formattedCreatedAt = loanInFocus?.createdAt
    ? new Date(loanInFocus.createdAt * 1000).toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : null;
  const formattedPurpose = formatLabel(loanInFocus?.purpose ?? null);
  const loanRateDisplay = loanInFocus ? deriveDisplayRate(loanInFocus.quotedRate ?? null, loanInFocus.interestRate) : null;
  const repaymentCta = loanInFocus
    ? ['active', 'disbursed'].includes(loanInFocus.backendStatus)
      ? 'View Repayments'
      : loanInFocus.backendStatus === 'approved'
      ? 'Prepare for Disbursement'
      : ['pending', 'submitted'].includes(loanInFocus.backendStatus)
      ? 'Track Application'
      : loanInFocus.backendStatus === 'completed' || loanInFocus.backendStatus === 'settled'
      ? 'View Completion Details'
      : 'View Details'
    : 'View Details';

  // Show loading skeleton on initial load
  if (initialLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-green-50 to-teal-50 p-4">
        <div className="max-w-md mx-auto">
          <DashboardSkeleton />
        </div>
      </div>
    );
  }

  // Show error state if critical data failed to load
  if (scoreError && !greenScore) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-green-50 to-teal-50 p-4">
        <div className="max-w-md mx-auto">
          <ErrorState
            title="Unable to load dashboard"
            description="We're having trouble loading your GreenScore and dashboard data."
            action={{
              label: "Try Again",
              onClick: () => {
                setInitialLoading(true);
                fetchCurrentScore().finally(() => setInitialLoading(false));
              }
            }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-green-50 to-teal-50 p-4 relative overflow-hidden">
      {/* Skip Link for screen readers */}
      <SkipLink href="#main-content">Skip to main content</SkipLink>

      {/* Animated Background Elements - decorative only */}
      <div
        className={`absolute inset-0 bg-gradient-to-br from-green-400/10 via-emerald-400/10 to-teal-400/10 ${!prefersReducedMotion ? 'animate-pulse' : ''}`}
        aria-hidden="true"
      />
      <div
        className={`absolute top-10 right-10 w-20 h-20 bg-green-400/20 rounded-full blur-xl ${!prefersReducedMotion ? 'animate-bounce' : ''}`}
        aria-hidden="true"
      />
      <div
        className={`absolute bottom-20 left-10 w-16 h-16 bg-teal-400/20 rounded-full blur-lg ${!prefersReducedMotion ? 'animate-pulse' : ''}`}
        aria-hidden="true"
      />

      <div className="relative z-10 max-w-md mx-auto space-y-4">
        {/* Enhanced Header */}
        <header className={`flex items-center justify-between ${!prefersReducedMotion ? 'animate-slide-down' : ''}`}>
          <Button
            variant="ghost"
            size="icon"
            onClick={onBack}
            className={cn("hover:bg-white/50 hover:backdrop-blur-sm transition-all", focusVisibleClasses)}
            aria-label="Go back to previous page"
          >
            <ArrowLeft className="w-5 h-5" />
            <VisuallyHidden>Back</VisuallyHidden>
          </Button>
          <div className="flex items-center space-x-2 p-2 rounded-xl bg-white/70 backdrop-blur-sm shadow-lg">
            <AccessibleIcon label="GreenCredit application logo" decorative>
              <div className="relative">
                <Leaf className={`w-6 h-6 text-green-600 ${!prefersReducedMotion ? 'animate-pulse' : ''}`} />
                <div className={`absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full ${!prefersReducedMotion ? 'animate-ping' : ''}`} />
              </div>
            </AccessibleIcon>
            <span className="text-lg font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">GreenCredit</span>
          </div>
          <div className="w-10" />
        </header>

        {/* Main Content */}
        <main id="main-content" className="space-y-4"
              role="main"
              aria-label="SME Dashboard"
        >

        {/* Enhanced Welcome */}
        <div className="text-center space-y-3 animate-fade-in p-4 rounded-2xl bg-white/60 backdrop-blur-sm shadow-lg border border-white/50">
          <div className="flex items-center justify-center space-x-2">
            <Sparkles className="w-5 h-5 text-yellow-500 animate-bounce" />
            <h1 className="text-2xl font-bold text-gray-900">Welcome back, {user.name.split(' ')[0]}!</h1>
            <Sparkles className="w-5 h-5 text-yellow-500 animate-bounce" style={{ animationDelay: '0.5s' }} />
          </div>
          <p className="text-gray-600 font-medium">{user.businessName} • {user.location}</p>
          
          {/* Achievement Streak */}
          <div className="flex items-center justify-center space-x-2 mt-2">
            <Flame className="w-4 h-4 text-orange-500 animate-pulse" />
            <span className="text-xs font-medium text-orange-600">5-day eco streak!</span>
            <Trophy className="w-4 h-4 text-yellow-500 animate-bounce" />
          </div>
        </div>

        {/* Enhanced GreenScore Card */}
        <section aria-labelledby="greenscore-title">
          <Card className={`relative overflow-hidden border-2 ${user.greenScore >= 70 ? 'border-green-300' : 'border-yellow-300'} bg-gradient-to-br from-white/80 to-white/60 backdrop-blur-sm shadow-xl hover:shadow-2xl transition-all duration-300 ${!prefersReducedMotion ? 'hover:scale-105 animate-fade-in' : ''}`} style={{ animationDelay: '0.2s' }}>
            {/* Glowing Effect */}
            <div className={`absolute inset-0 bg-gradient-to-br ${user.greenScore >= 70 ? 'from-green-400/20 to-emerald-400/20' : 'from-yellow-400/20 to-orange-400/20'} blur-sm`} aria-hidden="true" />
          
          <CardContent className="relative pt-6">
            <div className="text-center space-y-4">
              <div className="space-y-4">
                {/* Accessible Progress Ring */}
                <div className="relative w-36 h-36 mx-auto">
                  {/* Glowing Ring - decorative */}
                  <div className={`absolute inset-0 rounded-full bg-gradient-to-r ${user.greenScore >= 70 ? 'from-green-400 to-emerald-400' : 'from-yellow-400 to-orange-400'} blur-md opacity-30 ${!prefersReducedMotion ? 'animate-pulse' : ''}`} aria-hidden="true" />

                  {/* Score Circle with Animation */}
                  <div className="relative w-full h-full">
                    <svg
                      className="transform -rotate-90 w-36 h-36"
                      role="img"
                      aria-labelledby="greenscore-title"
                      aria-describedby="greenscore-description"
                    >
                      <title id="greenscore-title">GreenScore Progress</title>
                      <desc id="greenscore-description">Your current sustainability score is {user.greenScore} out of 100</desc>
                      <circle
                        cx="72"
                        cy="72"
                        r="64"
                        stroke="currentColor"
                        strokeWidth="6"
                        fill="none"
                        className="text-gray-200"
                      />
                      <circle
                        cx="72"
                        cy="72"
                        r="64"
                        stroke="url(#gradient)"
                        strokeWidth="6"
                        fill="none"
                        strokeDasharray={`${2 * Math.PI * 64}`}
                        strokeDashoffset={`${2 * Math.PI * 64 * (1 - user.greenScore / 100)}`}
                        strokeLinecap="round"
                        className={`${!prefersReducedMotion ? 'transition-all duration-1000 ease-out' : ''}`}
                      />
                      <defs>
                        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor={user.greenScore >= 70 ? '#10B981' : '#F59E0B'} />
                          <stop offset="100%" stopColor={user.greenScore >= 70 ? '#059669' : '#EAB308'} />
                        </linearGradient>
                      </defs>
                    </svg>

                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center space-y-1">
                        <div className={`text-4xl font-bold ${getScoreColor(user.greenScore)} ${!prefersReducedMotion ? 'animate-pulse' : ''}`}>
                          {user.greenScore}
                        </div>
                        <div className="text-xs text-gray-600 font-medium">GreenScore</div>
                        {user.greenScore >= 70 && (
                          <AccessibleIcon label="Excellent score achievement" decorative>
                            <Star className={`w-4 h-4 mx-auto text-yellow-500 ${!prefersReducedMotion ? 'animate-bounce' : ''}`} />
                          </AccessibleIcon>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Screen reader friendly progress */}
                <VisuallyHidden>
                  <AccessibleProgress
                    value={user.greenScore}
                    max={100}
                    label="Your GreenScore sustainability rating"
                  />
                </VisuallyHidden>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center justify-center space-x-2">
                  <Badge variant={user.greenScore >= 70 ? 'default' : 'secondary'} className={`text-sm font-bold px-4 py-2 ${user.greenScore >= 70 ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white' : 'bg-gradient-to-r from-yellow-500 to-orange-600 text-white'} border-0 shadow-lg`}>
                    {user.greenScore >= 80 ? '🏆 Excellent' : user.greenScore >= 60 ? '⭐ Good' : user.greenScore >= 40 ? '📈 Fair' : '🎯 Improving'}
                  </Badge>
                </div>
                
                <div className="flex items-center justify-center space-x-4 text-xs">
                  <div className="flex items-center space-x-1">
                    <CheckCircle className="w-3 h-3 text-green-500" />
                    <span className="text-gray-600">{user.ecoActions.filter(a => a.verified).length} verified</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Target className="w-3 h-3 text-blue-500" />
                    <span className="text-gray-600">Next: {100 - user.greenScore} pts</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

        {/* Enhanced Category Tiles */}
        <div className="grid grid-cols-2 gap-3 animate-slide-up" style={{ animationDelay: '0.4s' }}>
          {ecoCategories.map((category) => {
            const Icon = category.icon;
            return (
              <Card key={category.name} className="group relative overflow-hidden bg-white/70 backdrop-blur-sm border border-white/50 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 hover:-rotate-1">
                {/* Gradient Background */}
                <div className={`absolute inset-0 bg-gradient-to-br ${
                  category.name === 'Energy' ? 'from-yellow-100/50 to-orange-100/50' :
                  category.name === 'Water' ? 'from-blue-100/50 to-cyan-100/50' :
                  category.name === 'Waste' ? 'from-green-100/50 to-emerald-100/50' :
                  'from-purple-100/50 to-pink-100/50'
                } opacity-0 group-hover:opacity-100 transition-opacity`} />
                
                <CardContent className="relative p-4 text-center space-y-3">
                  <div className={`w-12 h-12 mx-auto rounded-xl bg-gradient-to-br ${
                    category.name === 'Energy' ? 'from-yellow-400 to-orange-500' :
                    category.name === 'Water' ? 'from-blue-400 to-cyan-500' :
                    category.name === 'Waste' ? 'from-green-400 to-emerald-500' :
                    'from-purple-400 to-pink-500'
                  } flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  
                  <div className="text-sm font-bold text-gray-800">{category.name}</div>
                  
                  <div className="space-y-2">
                    <div className={`text-xl font-bold ${getScoreColor(category.score)} group-hover:scale-110 transition-transform`}>
                      {category.score}
                    </div>
                    <div className="relative">
                      <Progress value={category.score} className="h-2 bg-gray-200" />
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/50 to-transparent animate-shimmer" />
                    </div>
                  </div>
                  
                  {category.score >= 80 && (
                    <div className="flex justify-center">
                      <Star className="w-4 h-4 text-yellow-500 animate-bounce" />
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Enhanced Quick Actions */}
        <section aria-labelledby="quick-actions-title">
          <VisuallyHidden>
            <h2 id="quick-actions-title">Quick Actions</h2>
          </VisuallyHidden>
          <div className={`grid grid-cols-2 gap-4 ${!prefersReducedMotion ? 'animate-slide-up' : ''}`} style={{ animationDelay: '0.6s' }}>
            <Button
              onClick={onUploadEvidence}
              className={cn(
                "group relative h-24 bg-gradient-to-br from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300 overflow-hidden",
                !prefersReducedMotion && "transform hover:scale-105 hover:-rotate-1",
                focusVisibleClasses
              )}
              aria-label="Upload sustainability evidence to boost your GreenScore"
            >
            {/* Animated Background */}
            <div className="absolute inset-0 bg-gradient-to-r from-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
            
            <div className="relative flex flex-col items-center space-y-2">
              <div className="p-2 bg-white/20 rounded-xl group-hover:scale-110 transition-transform">
                <Camera className="w-6 h-6 animate-pulse" />
              </div>
              <span className="text-sm font-bold">Upload Evidence</span>
              <div className="flex space-x-1">
                <Sparkles className="w-3 h-3 animate-pulse" />
                <span className="text-xs opacity-90">+15 pts</span>
                <Sparkles className="w-3 h-3 animate-pulse" style={{ animationDelay: '0.5s' }} />
              </div>
            </div>
          </Button>
          
          <Button 
            onClick={onViewLoans}
            className="group relative h-24 bg-white/80 backdrop-blur-sm border-2 border-green-400 text-green-600 hover:bg-gradient-to-br hover:from-green-500 hover:to-emerald-600 hover:text-white font-bold rounded-2xl shadow-xl hover:shadow-2xl transform hover:scale-105 hover:rotate-1 transition-all duration-300 overflow-hidden"
          >
            {/* Animated Background */}
            <div className="absolute inset-0 bg-gradient-to-r from-green-400/20 to-emerald-400/20 opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
            
            <div className="relative flex flex-col items-center space-y-2">
              <div className="p-2 bg-green-100 group-hover:bg-white/20 rounded-xl group-hover:scale-110 transition-all">
                <DollarSign className="w-6 h-6" />
              </div>
              <span className="text-sm font-bold">View Loans</span>
              <div className="flex items-center space-x-1">
                <TrendingUp className="w-3 h-3" />
                <span className="text-xs opacity-90">Better rates</span>
              </div>
            </div>
          </Button>
        </div>

        {/* Loan Status */}
        {loanInFocus && (
          <Card className={tone.card}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className={`text-sm flex items-center space-x-2 ${tone.label}`}>
                  <StatusIcon className="w-4 h-4" />
                  <span>{loanStatusInfo.label}</span>
                </CardTitle>
                {loanInFocus.backendStatus && (
                  <Badge className={`${tone.badge} uppercase tracking-wide text-[10px]`}>
                    {formatLabel(loanInFocus.backendStatus)}
                  </Badge>
                )}
              </div>
              {formattedCreatedAt && (
                <CardDescription className="text-xs text-gray-600">
                  Requested on {formattedCreatedAt}
                </CardDescription>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">Loan Amount</p>
                  <p className="text-lg font-bold">KES {loanInFocus.amount.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-gray-600">Interest Rate</p>
                  <p className={`text-lg font-bold ${loanRateDisplay != null ? 'text-green-600' : 'text-gray-500'}`}>
                    {loanRateDisplay != null ? `${loanRateDisplay}% APR` : 'Rate pending'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">Repayment Term</p>
                  <p className="text-sm font-medium">{loanInFocus.term} months</p>
                </div>
                <div>
                  <p className="text-gray-600">Purpose</p>
                  <p className="text-sm font-medium">{formattedPurpose}</p>
                </div>
              </div>
              {loanStatusInfo.helper && (
                <div className={`p-3 rounded-lg border text-sm font-medium ${tone.helper}`}>
                  {loanStatusInfo.helper}
                </div>
              )}
              <Button
                onClick={onViewRepayments}
                variant="outline"
                size="sm"
                className="w-full border-blue-600 text-blue-600 hover:bg-blue-100"
              >
                {repaymentCta}
              </Button>
            </CardContent>
          </Card>
        )}
      </section>

        {/* Enhanced Improvement Tips */}
        <Card className="relative overflow-hidden bg-gradient-to-br from-yellow-50/80 to-orange-50/80 backdrop-blur-sm border-2 border-yellow-200 shadow-xl animate-slide-up" style={{ animationDelay: '0.8s' }}>
          {/* Decorative Elements */}
          <div className="absolute top-2 right-2">
            <Gift className="w-6 h-6 text-yellow-500 animate-bounce" />
          </div>

          <CardHeader className="pb-3">
            <CardTitle className="text-base text-yellow-800 flex items-center space-x-2 font-bold">
              <div className="p-2 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-xl">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <span>Boost Your Score</span>
              <Sparkles className="w-4 h-4 text-yellow-600 animate-pulse" />
              {loadingRecommendations && <Spinner size="sm" />}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <LoadingOverlay isLoading={loadingRecommendations} message="Loading personalized recommendations...">
              {improvementTips.slice(0, 2).map((tip, index) => (
                <div key={index} className="group p-3 bg-white/60 backdrop-blur-sm rounded-xl border border-white/50 hover:bg-white/80 hover:scale-105 transition-all duration-200">
                  <div className="flex justify-between items-center">
                    <div className="space-y-1">
                      <div className="text-sm font-bold text-gray-800 group-hover:text-yellow-800 transition-colors">{tip.action}</div>
                      <div className="text-xs text-gray-600">{tip.description}</div>
                    </div>
                    <div className="flex flex-col items-center space-y-1">
                      <Badge className="bg-gradient-to-r from-green-500 to-emerald-600 text-white border-0 font-bold text-xs px-3 py-1 shadow-lg animate-pulse">
                        {tip.points}
                      </Badge>
                      <Star className="w-3 h-3 text-yellow-500" />
                    </div>
                  </div>
                </div>
              ))}
            </LoadingOverlay>
            <LoadingButton
              loading={loadingRecommendations}
              className="w-full text-sm bg-gradient-to-r from-yellow-500 to-orange-600 hover:from-yellow-600 hover:to-orange-700 text-white font-bold py-3 rounded-xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
              onClick={() => fetchRecommendations()}
            >
              <Target className="w-4 h-4 mr-2" />
              View All Tips
              <Sparkles className="w-4 h-4 ml-2 animate-pulse" />
            </LoadingButton>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        {user.ecoActions.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Recent Eco-Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {user.ecoActions.slice(-3).map((action) => (
                <div key={action.id} className="flex justify-between items-center">
                  <div className="space-y-1">
                    <div className="text-sm font-medium">{action.description}</div>
                    <div className="text-xs text-gray-500">{action.date} • {action.impact}</div>
                  </div>
                  <Badge variant={action.verified ? 'default' : 'secondary'} className="text-xs">
                    {action.verified ? 'Verified' : 'Pending'}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

      </main>

      {/* Custom CSS Animations  */}
      <style>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes slide-up {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes slide-down {
          from { opacity: 0; transform: translateY(-20px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }

        .animate-fade-in {
          animation: fade-in 0.8s ease-out forwards;
        }

        .animate-slide-up {
          animation: slide-up 0.8s ease-out forwards;
        }

        .animate-slide-down {
          animation: slide-down 0.6s ease-out forwards;
        }

        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
      `}</style>
    </div>
    </div>
  );
}


