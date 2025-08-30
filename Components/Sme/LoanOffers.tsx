import { useState } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Slider } from '../ui/slider';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { SMEUser } from '../SMEApp';
import { ArrowLeft, DollarSign, TrendingDown, Clock, CheckCircle, Calculator } from 'lucide-react';

interface LoanOffersProps {
  user: SMEUser;
  onBack: () => void;
  onApplyForLoan: (loan: {
    amount: number;
    interestRate: number;
    term: number;
    purpose: string;
  }) => void;
}

export function LoanOffers({ user, onBack, onApplyForLoan }: LoanOffersProps) {
  const [selectedAmount, setSelectedAmount] = useState([50000]);
  const [selectedTerm, setSelectedTerm] = useState('12');
  const [loanPurpose, setLoanPurpose] = useState('');
  const [showCalculator, setShowCalculator] = useState(false);

  // Calculate interest rate based on GreenScore
  const baseRate = 18; // Base rate in Kenya
  const getDiscountedRate = (greenScore: number) => {
    if (greenScore >= 80) return baseRate - 6; // 12%
    if (greenScore >= 70) return baseRate - 4; // 14%
    if (greenScore >= 60) return baseRate - 3; // 15%
    if (greenScore >= 50) return baseRate - 2; // 16%
    return baseRate - 1; // 17%
  };

  const discountedRate = getDiscountedRate(user.greenScore);
  const savings = baseRate - discountedRate;

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

  const calculateMonthlyPayment = (amount: number, rate: number, termMonths: number) => {
    const monthlyRate = rate / 100 / 12;
    const payment = (amount * monthlyRate * Math.pow(1 + monthlyRate, termMonths)) / 
                   (Math.pow(1 + monthlyRate, termMonths) - 1);
    return payment;
  };

  const monthlyPayment = calculateMonthlyPayment(selectedAmount[0], discountedRate, parseInt(selectedTerm));
  const totalPayment = monthlyPayment * parseInt(selectedTerm);
  const totalInterest = totalPayment - selectedAmount[0];

  const handleApply = () => {
    if (!loanPurpose) return;
    
    onApplyForLoan({
      amount: selectedAmount[0],
      interestRate: discountedRate,
      term: parseInt(selectedTerm),
      purpose: loanPurpose
    });
  };

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
          </div>
          <div className="w-10" />
        </div>

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
                    {savings}% Interest Discount Applied!
                  </p>
                  <p className="text-xs text-green-700">
                    Standard rate: {baseRate}% → Your rate: {discountedRate}%
                  </p>
                </div>
              </div>
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
            {/* Loan Amount */}
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

            {/* Loan Term */}
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

            {/* Loan Purpose */}
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
                  KES {monthlyPayment.toLocaleString(undefined, {maximumFractionDigits: 0})}
                </p>
              </div>
              <div>
                <p className="text-gray-600">Interest Rate</p>
                <p className="text-lg font-bold text-green-600">
                  {discountedRate}% APR
                </p>
              </div>
              <div>
                <p className="text-gray-600">Total Interest</p>
                <p className="text-sm font-medium">
                  KES {totalInterest.toLocaleString(undefined, {maximumFractionDigits: 0})}
                </p>
              </div>
              <div>
                <p className="text-gray-600">Total Payment</p>
                <p className="text-sm font-medium">
                  KES {totalPayment.toLocaleString(undefined, {maximumFractionDigits: 0})}
                </p>
              </div>
            </div>

            <div className="pt-3 border-t border-blue-200">
              <div className="flex items-center space-x-2 text-green-600">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm font-medium">
                  You save KES {((monthlyPayment * parseInt(selectedTerm) * savings / 100)).toLocaleString(undefined, {maximumFractionDigits: 0})} vs standard rate
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
        <Button 
          onClick={handleApply}
          disabled={!loanPurpose}
          className="w-full bg-green-600 hover:bg-green-700 h-12"
        >
          Apply for Loan
        </Button>

        <div className="text-center">
          <p className="text-xs text-gray-500">
            Subject to credit assessment and approval. Terms and conditions apply.
          </p>
        </div>
      </div>
    </div>
  );
}