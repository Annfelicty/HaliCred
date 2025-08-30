import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { SMEUser } from '../SMEApp';
import { 
  ArrowLeft, 
  DollarSign, 
  Calendar, 
  Leaf, 
  TrendingUp,
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

export function RepaymentTracker({ user, onBack }: RepaymentTrackerProps) {
  const activeLoan = user.loanApplications.find(loan => loan.status === 'active') || 
                    user.loanApplications.find(loan => loan.status === 'pending');
  
  if (!activeLoan) {
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
                <h2 className="text-lg font-medium">No Active Loans</h2>
                <p className="text-sm text-gray-600">Apply for a loan to start tracking repayments</p>
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

  // Mock repayment data
  const totalAmount = activeLoan.amount;
  const monthlyPayment = Math.round(totalAmount * (activeLoan.interestRate / 100 / 12 * Math.pow(1 + activeLoan.interestRate / 100 / 12, activeLoan.term)) / (Math.pow(1 + activeLoan.interestRate / 100 / 12, activeLoan.term) - 1));
  const paidAmount = activeLoan.status === 'active' ? Math.round(totalAmount * 0.3) : 0;
  const remainingAmount = totalAmount - paidAmount;
  const progressPercent = (paidAmount / totalAmount) * 100;
  
  const nextPaymentDate = new Date();
  nextPaymentDate.setDate(nextPaymentDate.getDate() + 15);

  // Mock eco-impact data
  const ecoImpact = {
    co2Saved: Math.round(user.ecoActions.length * 3.2 + Math.random() * 2),
    waterSaved: Math.round(user.ecoActions.length * 450 + Math.random() * 200),
    energySaved: Math.round(user.ecoActions.length * 1200 + Math.random() * 400)
  };

  const recentPayments = activeLoan.status === 'active' ? [
    { date: '15 Jan 2024', amount: monthlyPayment, status: 'paid' },
    { date: '15 Dec 2023', amount: monthlyPayment, status: 'paid' },
    { date: '15 Nov 2023', amount: monthlyPayment, status: 'paid' }
  ] : [];

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

        {/* Loan Status */}
        <Card className={`${activeLoan.status === 'pending' ? 'border-yellow-200 bg-yellow-50' : 'border-blue-200 bg-blue-50'}`}>
          <CardHeader>
            <CardTitle className="text-base flex items-center space-x-2">
              {activeLoan.status === 'pending' ? (
                <Clock className="w-5 h-5 text-yellow-600" />
              ) : (
                <CheckCircle className="w-5 h-5 text-blue-600" />
              )}
              <span className={activeLoan.status === 'pending' ? 'text-yellow-800' : 'text-blue-800'}>
                {activeLoan.status === 'pending' ? 'Application Pending' : 'Active Loan'}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Loan Amount</p>
                <p className="text-lg font-bold">KES {totalAmount.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Interest Rate</p>
                <p className="text-lg font-bold text-green-600">{activeLoan.interestRate}% APR</p>
              </div>
            </div>
            
            {activeLoan.status === 'pending' && (
              <div className="p-3 bg-yellow-100 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  Your application is being reviewed. You'll be notified within 24 hours.
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {activeLoan.status === 'active' && (
          <>
            {/* Repayment Progress */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Repayment Progress</CardTitle>
                <CardDescription>Track your loan repayment journey</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Paid: KES {paidAmount.toLocaleString()}</span>
                    <span>Remaining: KES {remainingAmount.toLocaleString()}</span>
                  </div>
                  <Progress value={progressPercent} className="h-3" />
                  <div className="text-center">
                    <span className="text-sm font-medium">{Math.round(progressPercent)}% Complete</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-2 border-t">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">{activeLoan.term - Math.floor(activeLoan.term * progressPercent / 100)}</p>
                    <p className="text-xs text-gray-600">Months Remaining</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">KES {monthlyPayment.toLocaleString()}</p>
                    <p className="text-xs text-gray-600">Monthly Payment</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Next Payment */}
            <Card className="border-orange-200 bg-orange-50">
              <CardContent className="pt-4">
                <div className="flex items-center space-x-3">
                  <Calendar className="w-6 h-6 text-orange-600" />
                  <div>
                    <p className="font-medium text-orange-800">Next Payment Due</p>
                    <p className="text-sm text-orange-700">
                      {nextPaymentDate.toLocaleDateString('en-GB', { 
                        day: 'numeric', 
                        month: 'short', 
                        year: 'numeric' 
                      })} - KES {monthlyPayment.toLocaleString()}
                    </p>
                  </div>
                </div>
                <Button size="sm" className="w-full mt-3 bg-orange-600 hover:bg-orange-700">
                  Pay Now via M-Pesa
                </Button>
              </CardContent>
            </Card>

            {/* Recent Payments */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Recent Payments</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {recentPayments.map((payment, index) => (
                  <div key={index} className="flex items-center justify-between py-2">
                    <div className="flex items-center space-x-3">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      <div>
                        <p className="text-sm font-medium">{payment.date}</p>
                        <p className="text-xs text-gray-500">Payment successful</p>
                      </div>
                    </div>
                    <p className="font-medium">KES {payment.amount.toLocaleString()}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </>
        )}

        {/* Eco Impact Tracker */}
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="text-base text-green-800 flex items-center space-x-2">
              <Leaf className="w-5 h-5" />
              <span>Environmental Impact</span>
            </CardTitle>
            <CardDescription className="text-green-700">
              Your positive impact on the environment
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
                <p className="text-lg font-bold text-blue-600">{ecoImpact.waterSaved}L</p>
                <p className="text-xs text-gray-600">Water Saved</p>
              </div>
              
              <div className="text-center p-3 bg-white rounded-lg border border-yellow-200">
                <div className="flex items-center justify-center w-8 h-8 bg-yellow-100 rounded-full mx-auto mb-2">
                  <Zap className="w-4 h-4 text-yellow-600" />
                </div>
                <p className="text-lg font-bold text-yellow-600">{ecoImpact.energySaved}</p>
                <p className="text-xs text-gray-600">kWh Saved</p>
              </div>
            </div>
            
            <div className="p-3 bg-white rounded-lg border border-green-200">
              <p className="text-sm text-green-800 font-medium mb-1">
                Keep improving your GreenScore for better rates!
              </p>
              <p className="text-xs text-green-700">
                Each verified eco-action helps reduce your interest rate on future loans.
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