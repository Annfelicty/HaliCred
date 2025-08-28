import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { BankUser, LoanApplication } from '../BankApp';
import { 
  ArrowLeft, 
  Building2, 
  Users, 
  DollarSign, 
  TrendingUp, 
  FileText, 
  PieChart, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Leaf,
  Sparkles,
  Shield,
  BarChart3,
  Target,
  Zap
} from 'lucide-react';

interface BankDashboardProps {
  user: BankUser;
  applications: LoanApplication[];
  onViewQueue: () => void;
  onViewPortfolio: () => void;
  onBack: () => void;
}

export function BankDashboard({ user, applications, onViewQueue, onViewPortfolio, onBack }: BankDashboardProps) {
  // Calculate metrics
  const pendingApps = applications.filter(app => app.status === 'pending').length;
  const underReviewApps = applications.filter(app => app.status === 'under_review').length;
  const approvedApps = applications.filter(app => app.status === 'approved' || app.status === 'disbursed').length;
  const totalAmount = applications.reduce((sum, app) => sum + app.amount, 0);
  const avgGreenScore = Math.round(applications.reduce((sum, app) => sum + app.greenScore, 0) / applications.length);
  const highRiskApps = applications.filter(app => app.riskAssessment.fraudRisk === 'high' || app.riskAssessment.fraudRisk === 'medium').length;

  // Calculate eco impact
  const totalCO2Saved = Math.round(applications.length * 4.2 + Math.random() * 10);
  const totalWaterSaved = Math.round(applications.length * 1200 + Math.random() * 500);

  const quickStats = [
    { label: 'Pending Applications', value: pendingApps, icon: Clock, color: 'text-yellow-600', bgColor: 'bg-yellow-50' },
    { label: 'Under Review', value: underReviewApps, icon: FileText, color: 'text-blue-600', bgColor: 'bg-blue-50' },
    { label: 'Approved Today', value: approvedApps, icon: CheckCircle, color: 'text-green-600', bgColor: 'bg-green-50' },
    { label: 'High Risk', value: highRiskApps, icon: AlertTriangle, color: 'text-red-600', bgColor: 'bg-red-50' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/50 p-4 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-400/5 via-blue-400/5 to-indigo-400/5 animate-pulse" />
      <div className="absolute top-20 right-20 w-40 h-40 bg-blue-400/10 rounded-full blur-3xl animate-bounce" />
      <div className="absolute bottom-20 left-20 w-32 h-32 bg-slate-400/10 rounded-full blur-2xl animate-pulse" />
      
      <div className="relative z-10 max-w-6xl mx-auto space-y-6">
        {/* Enhanced Header */}
        <div className="flex items-center justify-between animate-slide-down">
          <Button variant="ghost" size="icon" onClick={onBack} className="hover:bg-white/50 hover:backdrop-blur-sm hover:scale-110 transition-all">
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex items-center space-x-3 p-4 rounded-2xl bg-white/80 backdrop-blur-sm shadow-lg border border-white/50">
            <div className="relative">
              <Building2 className="w-7 h-7 text-slate-600 animate-pulse" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full animate-ping" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-slate-700 to-slate-900 bg-clip-text text-transparent">GreenCredit Bank Portal</span>
            <Shield className="w-6 h-6 text-green-600 animate-pulse" />
          </div>
          <Badge className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-bold px-4 py-2 text-sm shadow-lg animate-pulse">
            {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
          </Badge>
        </div>

        {/* Enhanced Welcome */}
        <div className="text-center space-y-4 animate-fade-in p-6 rounded-2xl bg-white/60 backdrop-blur-sm shadow-lg border border-white/50">
          <div className="flex items-center justify-center space-x-2">
            <Sparkles className="w-6 h-6 text-blue-500 animate-bounce" />
            <h1 className="text-3xl font-bold text-slate-900">Welcome back, {user.name}!</h1>
            <Sparkles className="w-6 h-6 text-blue-500 animate-bounce" style={{ animationDelay: '0.5s' }} />
          </div>
          <p className="text-slate-600 font-medium text-lg">Manage ESG-powered lending and drive sustainable finance</p>
          
          {/* Status Indicators */}
          <div className="flex items-center justify-center space-x-6 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
              <span className="text-slate-600 font-medium">All Systems Operational</span>
            </div>
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-yellow-500 animate-pulse" />
              <span className="text-slate-600 font-medium">Real-time Analytics</span>
            </div>
          </div>
        </div>

        {/* Enhanced Quick Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 animate-slide-up" style={{ animationDelay: '0.2s' }}>
          {quickStats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <Card key={index} className={`group relative overflow-hidden bg-white/80 backdrop-blur-sm border-2 border-white/50 shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105 hover:-rotate-1 ${stat.bgColor}`}>
                {/* Gradient Background */}
                <div className={`absolute inset-0 bg-gradient-to-br ${
                  stat.color.includes('yellow') ? 'from-yellow-400/20 to-orange-400/20' :
                  stat.color.includes('blue') ? 'from-blue-400/20 to-cyan-400/20' :
                  stat.color.includes('green') ? 'from-green-400/20 to-emerald-400/20' :
                  'from-red-400/20 to-pink-400/20'
                } opacity-0 group-hover:opacity-100 transition-opacity`} />
                
                <CardContent className="relative p-6 text-center space-y-3">
                  <div className={`w-12 h-12 mx-auto rounded-2xl bg-gradient-to-br ${
                    stat.color.includes('yellow') ? 'from-yellow-400 to-orange-500' :
                    stat.color.includes('blue') ? 'from-blue-400 to-cyan-500' :
                    stat.color.includes('green') ? 'from-green-400 to-emerald-500' :
                    'from-red-400 to-pink-500'
                  } flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="text-3xl font-bold text-slate-900 group-hover:scale-110 transition-transform">{stat.value}</div>
                  <div className="text-sm font-medium text-slate-600">{stat.label}</div>
                  
                  {/* Decorative Elements */}
                  {stat.value > 0 && (
                    <div className="flex justify-center">
                      <Sparkles className={`w-4 h-4 ${stat.color} animate-pulse`} />
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Key Metrics */}
        <div className="grid lg:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center space-x-2">
                <DollarSign className="w-5 h-5" />
                <span>Loan Portfolio</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Total Applications</p>
                  <p className="text-2xl font-bold">KES {totalAmount.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Avg Green Score</p>
                  <p className="text-2xl font-bold text-green-600">{avgGreenScore}</p>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Portfolio Health</span>
                  <span>{Math.round((approvedApps / applications.length) * 100)}% Approved</span>
                </div>
                <Progress value={(approvedApps / applications.length) * 100} className="h-2" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="text-base text-green-800 flex items-center space-x-2">
                <Leaf className="w-5 h-5" />
                <span>Environmental Impact</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-green-700">CO₂ Avoided</p>
                  <p className="text-2xl font-bold text-green-800">{totalCO2Saved} tCO₂</p>
                </div>
                <div>
                  <p className="text-sm text-green-700">Water Saved</p>
                  <p className="text-2xl font-bold text-green-800">{totalWaterSaved}L</p>
                </div>
              </div>
              
              <div className="p-3 bg-white rounded border border-green-200">
                <p className="text-sm text-green-800">
                  This month's loans will avoid approximately <strong>{Math.round(totalCO2Saved * 0.3)} tCO₂</strong> emissions
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Application Status Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Application Status Overview</CardTitle>
            <CardDescription>Current month application breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Pending Review</span>
                  <Badge variant="secondary">{pendingApps} apps</Badge>
                </div>
                <Progress value={(pendingApps / applications.length) * 100} className="h-2" />
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Under Review</span>
                  <Badge variant="outline" className="border-blue-600 text-blue-600">{underReviewApps} apps</Badge>
                </div>
                <Progress value={(underReviewApps / applications.length) * 100} className="h-2" />
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Approved</span>
                  <Badge className="bg-green-600">{approvedApps} apps</Badge>
                </div>
                <Progress value={(approvedApps / applications.length) * 100} className="h-2" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Enhanced Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-slide-up" style={{ animationDelay: '0.6s' }}>
          <Button 
            onClick={onViewQueue}
            className="group relative h-24 bg-gradient-to-br from-slate-700 to-slate-900 hover:from-slate-800 hover:to-black text-white font-bold rounded-2xl shadow-2xl hover:shadow-3xl transform hover:scale-105 hover:rotate-1 transition-all duration-300 overflow-hidden"
          >
            {/* Animated Background */}
            <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
            
            <div className="relative flex items-center space-x-4">
              <div className="p-3 bg-white/20 rounded-2xl group-hover:scale-110 transition-transform">
                <FileText className="w-8 h-8 animate-pulse" />
              </div>
              <div className="text-left space-y-1">
                <div className="text-lg font-bold">Review Applications</div>
                <div className="text-sm opacity-90 flex items-center space-x-2">
                  <Target className="w-4 h-4" />
                  <span>{pendingApps + underReviewApps} pending review</span>
                  <Sparkles className="w-4 h-4 animate-pulse" />
                </div>
              </div>
            </div>
          </Button>
          
          <Button 
            onClick={onViewPortfolio}
            className="group relative h-24 bg-white/90 backdrop-blur-sm border-2 border-slate-300 text-slate-700 hover:bg-gradient-to-br hover:from-slate-100 hover:to-slate-200 hover:text-slate-900 font-bold rounded-2xl shadow-2xl hover:shadow-3xl transform hover:scale-105 hover:-rotate-1 transition-all duration-300 overflow-hidden"
          >
            {/* Animated Background */}
            <div className="absolute inset-0 bg-gradient-to-r from-slate-200/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
            
            <div className="relative flex items-center space-x-4">
              <div className="p-3 bg-slate-100 group-hover:bg-slate-200 rounded-2xl group-hover:scale-110 transition-all">
                <PieChart className="w-8 h-8" />
              </div>
              <div className="text-left space-y-1">
                <div className="text-lg font-bold">Portfolio Dashboard</div>
                <div className="text-sm opacity-90 flex items-center space-x-2">
                  <BarChart3 className="w-4 h-4" />
                  <span>Analytics & ESG Reports</span>
                  <Leaf className="w-4 h-4 text-green-600 animate-pulse" />
                </div>
              </div>
            </div>
          </Button>
        </div>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Activity</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {applications.slice(0, 3).map((app) => (
              <div key={app.id} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
                <div className="space-y-1">
                  <div className="text-sm font-medium">{app.applicantName}</div>
                  <div className="text-xs text-gray-500">
                    {app.businessName} • KES {app.amount.toLocaleString()} • Score: {app.greenScore}
                  </div>
                </div>
                <Badge 
                  variant={app.status === 'approved' ? 'default' : app.status === 'pending' ? 'secondary' : 'outline'}
                  className={
                    app.status === 'approved' ? 'bg-green-600' : 
                    app.status === 'pending' ? 'bg-yellow-600' : ''
                  }
                >
                  {app.status.replace('_', ' ').charAt(0).toUpperCase() + app.status.replace('_', ' ').slice(1)}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
      
      {/* Custom CSS Animations */}
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
        
        .animate-fade-in {
          animation: fade-in 0.8s ease-out forwards;
        }
        
        .animate-slide-up {
          animation: slide-up 0.8s ease-out forwards;
        }
        
        .animate-slide-down {
          animation: slide-down 0.6s ease-out forwards;
        }
      `}</style>
    </div>
  );
}