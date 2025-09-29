import { useMemo } from 'react';
import { Button } from '../Ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../Ui/card';
import { Badge } from '../Ui/badge';
import { Progress } from '../Ui/progress';
import { SMEUser } from '../SMEApp';
import {
  ArrowLeft,
  DollarSign,
  Calendar,
  Leaf,
  CheckCircle,
  Clock,
  AlertCircle,
  Droplets,
  Zap
} from 'lucide-react';

interface RepaymentTrackerProps {
  user: SMEUser;
  onBack: () => void;
}

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
        helper: 'Awaiting disbursement to your preferred account.',
        tone: 'approved',
      };
    case 'disbursed':
    case 'active':
      return {
        label: 'Active Loan',
        helper: 'Make timely repayments to maintain your discounted rate.',
        tone: 'active',
      };
    case 'completed':
    case 'settled':
      return {
        label: 'Loan Completed',
        helper: 'Congratulations on closing out your facility.',
        tone: 'completed',
      };
    default:
      return {
        label: 'Loan Status',
        tone: 'neutral',
      };
  }
};

const toDisplayRate = (value: number | null | undefined): number | null => {
  if (typeof value !== 'number') {
    return null;
  }
  const normalized = value <= 1 ? value * 100 : value;
  return Math.round(normalized * 100) / 100;
};

const calculateMonthlyPayment = (amount: number, ratePercent: number, termMonths: number): number => {
  if (termMonths <= 0 || amount <= 0) {
    return 0;
  }
  const monthlyRate = ratePercent / 100 / 12;
  if (monthlyRate <= 0) {
    return amount / termMonths;
  }
  const numerator = amount * monthlyRate * Math.pow(1 + monthlyRate, termMonths);
  const denominator = Math.pow(1 + monthlyRate, termMonths) - 1;
  if (denominator === 0) {
    return amount / termMonths;
  }
  return numerator / denominator;
};

const monthsBetween = (start: Date, end: Date): number => {
  const yearDiff = end.getFullYear() - start.getFullYear();
  const monthDiff = end.getMonth() - start.getMonth();
  let months = yearDiff * 12 + monthDiff;
  if (end.getDate() < start.getDate()) {
    months -= 1;
  }
  return Math.max(months, 0);
};

const addMonths = (input: Date, count: number): Date => {
  const result = new Date(input.getTime());
  result.setMonth(result.getMonth() + count);
  return result;
};

const formatDate = (date: Date | null | undefined): string => {
  if (!date || Number.isNaN(date.getTime())) {
    return 'TBD';
  }
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
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

export function RepaymentTracker({ user, onBack }: RepaymentTrackerProps) {
  const loanInFocus = useMemo(() => {
    if (!user.loanApplications || user.loanApplications.length === 0) {
      return null;
    }
    const priority = ['active', 'disbursed', 'approved', 'pending', 'submitted', 'completed', 'settled'];
    for (const status of priority) {
      const match = user.loanApplications.find((loan) => {
        const backendStatus = loan.backendStatus?.toLowerCase();
        const normalizedStatus = loan.status?.toLowerCase();
        return backendStatus === status || normalizedStatus === status;
      });
      if (match) {
        return match;
      }
    }
    return user.loanApplications[0];
  }, [user.loanApplications]);

  const statusKey = loanInFocus?.backendStatus?.toLowerCase() || loanInFocus?.status?.toLowerCase() || 'unknown';
  const statusInfo = resolveLoanStatus(statusKey);
  const tone = toneClasses[statusInfo.tone];
const StatusIcon = statusInfo.tone === 'pending' ? Clock : statusInfo.tone === 'neutral' ? DollarSign : CheckCircle;

  const computedLoanMetrics = useMemo(() => {
    if (!loanInFocus) {
      return {
        originatedAt: null,
        quotedRate: null as number | null,
        monthlyPayment: 0,
        totalInstallments: 0,
        normalizedMonthsElapsed: 0,
        totalDue: 0,
        amountRepaid: 0,
        remainingBalance: 0,
        repaymentProgress: 0,
        progressPercent: 0,
        installmentsRemaining: 0,
        nextPaymentDate: null as Date | null,
        schedulePreview: { completed: [] as Date[], upcoming: [] as Date[] },
      };
    }

    const originatedAt = loanInFocus.createdAt ? new Date(loanInFocus.createdAt * 1000) : null;
    const quotedRate = toDisplayRate(loanInFocus.quotedRate ?? loanInFocus.interestRate ?? null);
    const totalInstallments = loanInFocus.term || loanInFocus.tenor || 0;
    const monthlyPayment = calculateMonthlyPayment(
      loanInFocus.amount,
      quotedRate ?? 0,
      totalInstallments
    );

    const now = new Date();
    const rawMonthsElapsed = originatedAt ? monthsBetween(originatedAt, now) : 0;
    const normalizedMonthsElapsed = statusInfo.tone === 'completed'
      ? totalInstallments
      : Math.min(totalInstallments, rawMonthsElapsed);

    const totalDue = monthlyPayment * totalInstallments;
    const amountRepaid = statusInfo.tone === 'completed'
      ? totalDue
      : Math.min(totalDue, monthlyPayment * normalizedMonthsElapsed);
    const remainingBalance = Math.max(totalDue - amountRepaid, 0);
    const progressPercent = Math.round(totalDue > 0 ? Math.min(1, amountRepaid / totalDue) * 100 : 0);
    const installmentsRemaining = Math.max(totalInstallments - normalizedMonthsElapsed, 0);

    const nextPaymentDate = (() => {
      if (!originatedAt) {
        return null;
      }
      if (statusInfo.tone === 'completed' || installmentsRemaining <= 0) {
        return null;
      }
      return addMonths(originatedAt, normalizedMonthsElapsed + 1);
    })();

    const schedulePreview = (() => {
      if (!originatedAt || totalInstallments <= 0) {
        return { completed: [] as Date[], upcoming: [] as Date[] };
      }
      const completedCount = Math.min(normalizedMonthsElapsed, totalInstallments);
      const upcomingCount = Math.max(totalInstallments - completedCount, 0);

      const completed = Array.from({ length: Math.min(3, completedCount) }, (_, index) => {
        const monthsAgo = completedCount - index;
        return addMonths(originatedAt, monthsAgo);
      });

      const upcoming = Array.from({ length: Math.min(3, upcomingCount) }, (_, index) => {
        const monthsAhead = normalizedMonthsElapsed + index + 1;
        return addMonths(originatedAt, monthsAhead);
      });

      return { completed, upcoming };
    })();

    return {
      originatedAt,
      quotedRate,
      monthlyPayment,
      totalInstallments,
      normalizedMonthsElapsed,
      amountRepaid,
      remainingBalance,
      progressPercent,
      installmentsRemaining,
      nextPaymentDate,
      schedulePreview,
    };
  }, [loanInFocus, statusInfo.tone]);

  const {
    originatedAt,
    quotedRate,
    monthlyPayment,
    totalInstallments,
    amountRepaid,
    remainingBalance,
    progressPercent,
    installmentsRemaining,
    nextPaymentDate,
    schedulePreview,
  } = computedLoanMetrics;

  if (!loanInFocus) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-teal-50 p-4">
        <div className="max-w-md mx-auto space-y-4">
          <div className="flex items-center justify-between">
            <Button variant="ghost" size="icon" onClick={onBack}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <span className="text-lg font-medium text-green-800">Loan Status</span>
            <div className="w-10" />
          </div>

          <Card>
            <CardContent className="pt-6 text-center space-y-4">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto">
                <DollarSign className="w-8 h-8 text-gray-400" />
              </div>
              <div>
                <h2 className="text-lg font-medium">No Loan Applications Yet</h2>
                <p className="text-sm text-gray-600">Apply for a facility to begin tracking repayments.</p>
              </div>
              <Button onClick={onBack} className="bg-green-600 hover:bg-green-700">
                Back to Dashboard
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const verifiedActions = user.ecoActions.filter((action) => action.verified).length;
  const totalActions = user.ecoActions.length;
  const ecoImpact = {
    co2Saved: Number((verifiedActions * 2.4).toFixed(1)),
    waterSaved: verifiedActions * 420,
    energySaved: verifiedActions * 940,
  };

  const hasRepaymentMetrics = statusInfo.tone === 'active' || statusInfo.tone === 'completed';

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-teal-50 p-4">
      <div className="max-w-md mx-auto space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex items-center space-x-2">
            <DollarSign className="w-6 h-6 text-green-600" />
            <span className="text-lg font-medium text-green-800">Loan Tracker</span>
          </div>
          <div className="w-10" />
        </div>

        {/* Loan Overview */}
        <Card className={tone.card}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className={`text-base flex items-center space-x-2 ${tone.label}`}>
                <StatusIcon className="w-5 h-5" />
                <span>{statusInfo.label}</span>
              </CardTitle>
              {loanInFocus.backendStatus && (
                <Badge className={`${tone.badge} uppercase tracking-wide text-[10px]`}>
                  {formatLabel(loanInFocus.backendStatus)}
                </Badge>
              )}
            </div>
            {originatedAt && (
              <CardDescription className="text-xs text-gray-600">
                Originated on {formatDate(originatedAt)}
              </CardDescription>
            )}
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Principal Amount</p>
                <p className="text-lg font-bold">KES {loanInFocus.amount.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-gray-600">Interest Rate</p>
                <p className={`text-lg font-bold ${quotedRate != null ? 'text-green-600' : 'text-gray-500'}`}>
                  {quotedRate != null ? `${quotedRate}% APR` : 'Rate pending'}
                </p>
              </div>
              <div>
                <p className="text-gray-600">Repayment Term</p>
                <p className="text-sm font-medium">{totalInstallments} months</p>
              </div>
              <div>
                <p className="text-gray-600">Purpose</p>
                <p className="text-sm font-medium">{formatLabel(loanInFocus.purpose)}</p>
              </div>
            </div>
            {statusInfo.helper && (
              <div className={`p-3 rounded-lg border text-sm font-medium ${tone.helper}`}>
                {statusInfo.helper}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Repayment Progress */}
        {hasRepaymentMetrics && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Repayment Progress</CardTitle>
              <CardDescription>
                Projected repayments based on your disbursement schedule
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Paid to date</span>
                  <span>KES {amountRepaid.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Balance remaining</span>
                  <span>KES {remainingBalance.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                </div>
                <Progress value={progressPercent} className="h-3" />
                <div className="text-center">
                  <span className="text-sm font-medium">{progressPercent}% Complete</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-2 border-t">
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">{installmentsRemaining}</p>
                  <p className="text-xs text-gray-600">Installments Remaining</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">KES {monthlyPayment.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
                  <p className="text-xs text-gray-600">Monthly Payment</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Next Payment / Application Timeline */}
        <Card className={statusInfo.tone === 'pending' ? 'border-yellow-200 bg-yellow-50' : 'border-orange-200 bg-orange-50'}>
          <CardContent className="pt-4 space-y-3">
            {statusInfo.tone === 'pending' || statusInfo.tone === 'approved' ? (
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div>
                  <p className="font-medium text-yellow-800">Application In Progress</p>
                  <p className="text-sm text-yellow-700">
                    We will notify you once underwriting is complete. Check back soon for repayment details.
                  </p>
                </div>
              </div>
            ) : nextPaymentDate ? (
              <div className="flex items-start space-x-3">
                <Calendar className="w-6 h-6 text-orange-600" />
                <div>
                  <p className="font-medium text-orange-800">Next Payment Due</p>
                  <p className="text-sm text-orange-700">
                    {formatDate(nextPaymentDate)} · KES {monthlyPayment.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex items-start space-x-3">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <div>
                  <p className="font-medium text-green-800">Schedule Complete</p>
                  <p className="text-sm text-green-700">No further payments are scheduled for this facility.</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Payment Schedule Snapshot */}
        {originatedAt && totalInstallments > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Payment Schedule Snapshot</CardTitle>
              <CardDescription>
                High-level view of completed and upcoming installments
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase text-gray-500">Recent Installments</p>
                {schedulePreview.completed.length === 0 ? (
                  <p className="text-sm text-gray-600">No installments recorded yet.</p>
                ) : (
                  <ul className="space-y-1 text-sm">
                    {schedulePreview.completed.map((date, index) => (
                      <li key={`completed-${index}`} className="flex items-center justify-between">
                        <span>{formatDate(date)}</span>
                        <span className="text-xs text-gray-500">Projected</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="pt-3 border-t space-y-2">
                <p className="text-xs font-semibold uppercase text-gray-500">Upcoming Installments</p>
                {schedulePreview.upcoming.length === 0 ? (
                  <p className="text-sm text-gray-600">You are up to date on this loan.</p>
                ) : (
                  <ul className="space-y-1 text-sm">
                    {schedulePreview.upcoming.map((date, index) => (
                      <li key={`upcoming-${index}`} className="flex items-center justify-between">
                        <span>{formatDate(date)}</span>
                        <span className="text-xs text-gray-500">Due</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Eco Impact Tracker */}
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="text-base text-green-800 flex items-center space-x-2">
              <Leaf className="w-5 h-5" />
              <span>Environmental Impact</span>
            </CardTitle>
            <CardDescription className="text-green-700">
              Verified eco-actions contributing to greener financing
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center p-3 bg-white rounded-lg border border-green-200">
                <div className="flex items-center justify-center w-8 h-8 bg-green-100 rounded-full mx-auto mb-2">
                  <Leaf className="w-4 h-4 text-green-600" />
                </div>
                <p className="text-lg font-bold text-green-600">{ecoImpact.co2Saved}</p>
                <p className="text-xs text-gray-600">tCO₂ Saved</p>
              </div>

              <div className="text-center p-3 bg-white rounded-lg border border-blue-200">
                <div className="flex items-center justify-center w-8 h-8 bg-blue-100 rounded-full mx-auto mb-2">
                  <Droplets className="w-4 h-4 text-blue-600" />
                </div>
                <p className="text-lg font-bold text-blue-600">{ecoImpact.waterSaved.toLocaleString()}L</p>
                <p className="text-xs text-gray-600">Water Saved</p>
              </div>

              <div className="text-center p-3 bg-white rounded-lg border border-yellow-200">
                <div className="flex items-center justify-center w-8 h-8 bg-yellow-100 rounded-full mx-auto mb-2">
                  <Zap className="w-4 h-4 text-yellow-600" />
                </div>
                <p className="text-lg font-bold text-yellow-600">{ecoImpact.energySaved.toLocaleString()}</p>
                <p className="text-xs text-gray-600">kWh Saved</p>
              </div>
            </div>

            <div className="p-3 bg-white rounded-lg border border-green-200">
              <p className="text-sm text-green-800 font-medium mb-1">
                {verifiedActions} of {totalActions} eco-actions verified
              </p>
              <p className="text-xs text-green-700">
                Each verified action unlocks better loan terms and lowers your climate footprint.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 gap-3">
          <Button variant="outline" className="border-green-600 text-green-600 hover:bg-green-50">
            Download Statement
          </Button>
          <Button variant="outline" className="border-blue-600 text-blue-600 hover:bg-blue-50">
            Contact Support
          </Button>
        </div>
      </div>
    </div>
  );
}
