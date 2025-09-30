import { useEffect, useMemo, useState } from 'react';
import { Button } from '../Ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../Ui/card';
import { Badge } from '../Ui/badge';
import { Slider } from '../Ui/slider';
import { Label } from '../Ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../Ui/select';
import { loans } from '../../lib/api';
import { SMEUser } from '../SMEApp';
import { ArrowLeft, DollarSign, TrendingDown, Clock, CheckCircle, Calculator, AlertCircle } from 'lucide-react';
import { PageLoadingSkeleton, ErrorState, LoadingButton, Spinner } from '../Ui/loading';

interface LoanQuoteOption {
  tenor: number;
  rate: number;
  discount_reason?: string;
}

interface LoanOffersProps {
  user: SMEUser;
  onBack: () => void;
  onApplyForLoan: (loan: {
    amount: number;
    term: number;
    purpose: string;
    estimatedRate: number;
  }) => Promise<void> | void;
}

const BASELINE_RATE = 18; // Reference standard rate (percentage)

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

export function LoanOffers({ user, onBack, onApplyForLoan }: LoanOffersProps) {
  const [selectedAmount, setSelectedAmount] = useState<number[]>([50000]);
  const [selectedTerm, setSelectedTerm] = useState<string>('12');
  const [loanPurpose, setLoanPurpose] = useState<string>('');
  const [quoteOptions, setQuoteOptions] = useState<LoanQuoteOption[]>([]);
  const [loadingQuotes, setLoadingQuotes] = useState<boolean>(true);
  const [quoteError, setQuoteError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [initialLoad, setInitialLoad] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    const fetchQuotes = async () => {
      const amount = selectedAmount[0];
      const tenor = parseInt(selectedTerm, 10);
      if (!Number.isFinite(amount) || !Number.isFinite(tenor)) {
        return;
      }
      setLoadingQuotes(true);
      setQuoteError(null);
      try {
        const response = await loans.getLoanOffers({ amount, tenor });
        if (!isMounted) {
          return;
        }
        if (response && Array.isArray(response.options)) {
          setQuoteOptions(response.options);
        } else {
          setQuoteOptions([]);
          setQuoteError('No loan offers are currently available for the selected amount and term.');
        }
      } catch (error) {
        console.error('Failed to fetch loan quotes:', error);
        if (isMounted) {
          setQuoteOptions([]);
          setQuoteError(error instanceof Error ? error.message : 'Failed to load loan offers.');
        }
      } finally {
        if (isMounted) {
          setLoadingQuotes(false);
          setInitialLoad(false);
        }
      }
    };

    fetchQuotes();

    return () => {
      isMounted = false;
    };
  }, [selectedAmount, selectedTerm]);

  const activeQuote = useMemo(() => {
    const tenor = parseInt(selectedTerm, 10);
    return quoteOptions.find((option) => option.tenor === tenor) ?? quoteOptions[0] ?? null;
  }, [quoteOptions, selectedTerm]);

  const quotedRate = useMemo(() => toDisplayRate(activeQuote?.rate), [activeQuote]);
  const appliedRate = quotedRate ?? Math.round((BASELINE_RATE - Math.max(0, Math.min(user.greenScore - 50, 30)) / 2) * 100) / 100;
  const rateSavings = quotedRate != null ? Math.max(0, Math.round((BASELINE_RATE - quotedRate) * 100) / 100) : null;

  const monthlyPayment = calculateMonthlyPayment(selectedAmount[0], appliedRate, parseInt(selectedTerm, 10));
  const totalPayment = monthlyPayment * parseInt(selectedTerm, 10);
  const totalInterest = totalPayment - selectedAmount[0];

  const loanPurposes = {
    farmer: [
      { value: 'equipment', label: 'Agricultural Equipment' },
      { value: 'seeds', label: 'Seeds & Fertilizers' },
      { value: 'irrigation', label: 'Irrigation System' },
      { value: 'storage', label: 'Storage & Processing' }
    ],
    salon: [
      { value: 'equipment', label: 'Salon Equipment' },
      { value: 'renovation', label: 'Shop Renovation' },
      { value: 'inventory', label: 'Product Inventory' },
      { value: 'expansion', label: 'Business Expansion' }
    ],
    welding: [
      { value: 'equipment', label: 'Welding Equipment' },
      { value: 'materials', label: 'Raw Materials' },
      { value: 'workshop', label: 'Workshop Setup' },
      { value: 'tools', label: 'Tools & Machinery' }
    ],
    other: [
      { value: 'equipment', label: 'Business Equipment' },
      { value: 'inventory', label: 'Inventory' },
      { value: 'expansion', label: 'Business Expansion' },
      { value: 'working_capital', label: 'Working Capital' }
    ]
  };

  const purposes = loanPurposes[user.businessType] || loanPurposes.other;

  const handleApply = async () => {
    if (!loanPurpose || submitting) {
      return;
    }
    const amount = selectedAmount[0];
    const term = parseInt(selectedTerm, 10);
    const estimatedRate = appliedRate;

    try {
      setSubmitting(true);
      await onApplyForLoan({ amount, term, purpose: loanPurpose, estimatedRate });
    } catch (error) {
      console.error('Loan application failed:', error);
    } finally {
      setSubmitting(false);
    }
  };

  // Show loading skeleton on initial load
  if (initialLoad) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-teal-50 p-4">
        <div className="max-w-md mx-auto">
          <PageLoadingSkeleton />
        </div>
      </div>
    );
  }

  // Show error state if critical data failed to load
  if (quoteError && quoteOptions.length === 0 && !loadingQuotes) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-teal-50 p-4">
        <div className="max-w-md mx-auto">
          <div className="flex items-center justify-between mb-6">
            <Button variant="ghost" size="icon" onClick={onBack}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex items-center space-x-2">
              <DollarSign className="w-6 h-6 text-green-600" />
              <span className="text-lg font-medium text-green-800">Loan Offers</span>
            </div>
            <div className="w-10" />
          </div>
          <ErrorState
            title="Unable to load loan offers"
            description="We're having trouble loading loan offers for your selected amount and term."
            action={{
              label: "Try Again",
              onClick: () => {
                setQuoteError(null);
                setLoadingQuotes(true);
                setInitialLoad(true);
              }
            }}
          />
        </div>
      </div>
    );
  }

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
            <span className="text-lg font-medium text-green-800">Loan Offers</span>
            {loadingQuotes && <Spinner size="sm" />}
          </div>
          <div className="w-10" />
        </div>

        {quoteError && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="flex items-start space-x-3 py-4">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-700">{quoteError}</p>
                <p className="text-xs text-red-600">Modify your amount or term and try again.</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* GreenScore Benefits */}
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-green-800">Your GreenScore</span>
                <Badge className="bg-green-600 text-white">{user.greenScore}</Badge>
              </div>
              <div className="flex items-center space-x-2">
                <TrendingDown className="w-5 h-5 text-green-600" />
                <div>
                  <p className="text-sm font-medium text-green-800">
                    {rateSavings != null && rateSavings > 0
                      ? `${rateSavings}% Interest Discount Applied!`
                      : 'Personalized rate based on your GreenScore'}
                  </p>
                  <p className="text-xs text-green-700">
                    Standard rate: {BASELINE_RATE}% → Your rate:{' '}
                    {quotedRate != null ? `${quotedRate}%` : `${appliedRate}%`}
                  </p>
                </div>
              </div>
              {loadingQuotes && (
                <p className="text-xs text-green-600">Fetching the best offers for you…</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Loan Calculator */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center space-x-2">
              <Calculator className="w-5 h-5" />
              <span>Loan Calculator</span>
            </CardTitle>
            <CardDescription>Customize your loan amount and terms</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-3">
              <Label>Loan Amount: KES {selectedAmount[0].toLocaleString()}</Label>
              <Slider
                value={selectedAmount}
                onValueChange={setSelectedAmount}
                max={500000}
                min={10000}
                step={10000}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>KES 10K</span>
                <span>KES 500K</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Repayment Period</Label>
              <Select value={selectedTerm} onValueChange={setSelectedTerm}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="6">6 months</SelectItem>
                  <SelectItem value="12">12 months</SelectItem>
                  <SelectItem value="18">18 months</SelectItem>
                  <SelectItem value="24">24 months</SelectItem>
                  <SelectItem value="36">36 months</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Loan Purpose</Label>
              <Select value={loanPurpose} onValueChange={setLoanPurpose}>
                <SelectTrigger>
                  <SelectValue placeholder="Select purpose" />
                </SelectTrigger>
                <SelectContent>
                  {purposes.map((purpose) => (
                    <SelectItem key={purpose.value} value={purpose.value}>
                      {purpose.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Loan Summary */}
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="text-base text-blue-800">Loan Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Monthly Payment</p>
                <p className="text-lg font-bold text-blue-800">
                  KES {monthlyPayment.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
              </div>
              <div>
                <p className="text-gray-600">Interest Rate</p>
                <p className="text-lg font-bold text-green-600">
                  {appliedRate}% APR
                </p>
              </div>
              <div>
                <p className="text-gray-600">Total Interest</p>
                <p className="text-sm font-medium">
                  KES {totalInterest.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
              </div>
              <div>
                <p className="text-gray-600">Total Payment</p>
                <p className="text-sm font-medium">
                  KES {totalPayment.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </p>
              </div>
            </div>

            <div className="pt-3 border-t border-blue-200">
              <div className="flex items-center space-x-2 text-green-600">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm font-medium">
                  {rateSavings != null && rateSavings > 0
                    ? `You save approximately KES ${(
                        monthlyPayment * parseInt(selectedTerm, 10) * rateSavings
                      / BASELINE_RATE
                      ).toLocaleString(undefined, { maximumFractionDigits: 0 })} vs standard rate`
                    : 'Optimized repayment plan tailored to your GreenScore'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Features */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Loan Features</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { icon: Clock, text: 'Instant approval for qualified applicants' },
                { icon: DollarSign, text: 'No hidden fees or charges' },
                { icon: CheckCircle, text: 'Flexible repayment options' },
                { icon: TrendingDown, text: 'Rate reduction for improved GreenScore' }
              ].map((feature, index) => {
                const Icon = feature.icon;
                return (
                  <div key={index} className="flex items-center space-x-3">
                    <Icon className="w-4 h-4 text-green-600 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{feature.text}</span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Apply Button */}
        <LoadingButton
          loading={submitting}
          loadingText="Submitting application..."
          onClick={handleApply}
          disabled={!loanPurpose || loadingQuotes}
          className="w-full bg-green-600 hover:bg-green-700 h-12"
        >
          Apply for Loan
        </LoadingButton>

        <div className="text-center">
          <p className="text-xs text-gray-500">
            Subject to credit assessment and approval. Terms and conditions apply.
          </p>
        </div>
      </div>
    </div>
  );
}
