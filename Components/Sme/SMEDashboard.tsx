import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { SMEUser } from '../SMEApp';
import { 
  Leaf, 
  ArrowLeft, 
  Upload, 
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

interface SMEDashboardProps {
  user: SMEUser;
  onUploadEvidence: () => void;
  onViewLoans: () => void;
  onViewRepayments: () => void;
  onBack: () => void;
}

export function SMEDashboard({ user, onUploadEvidence, onViewLoans, onViewRepayments, onBack }: SMEDashboardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-50';
    if (score >= 60) return 'bg-yellow-50';
    return 'bg-red-50';
  };

  const ecoCategories = [
    { name: 'Energy', icon: Zap, score: Math.min(100, user.greenScore + Math.floor(Math.random() * 20)), color: 'text-yellow-600' },
    { name: 'Water', icon: Droplets, score: Math.min(100, user.greenScore + Math.floor(Math.random() * 20)), color: 'text-blue-600' },
    { name: 'Waste', icon: Recycle, score: Math.min(100, user.greenScore + Math.floor(Math.random() * 20)), color: 'text-green-600' },
    { name: 'Behavior', icon: User, score: Math.min(100, user.greenScore + Math.floor(Math.random() * 20)), color: 'text-purple-600' }
  ];

  const improvementTips = [
    { action: 'Install LED lighting', points: '+15 pts', description: 'Replace incandescent bulbs' },
    { action: 'Solar water heating', points: '+20 pts', description: 'Reduce electricity usage' },
    { action: 'Waste separation', points: '+10 pts', description: 'Sort organic vs recyclable' },
    { action: 'Energy audit', points: '+12 pts', description: 'Professional assessment' }
  ];

  const activeLoan = user.loanApplications.find(loan => loan.status === 'active');
  const pendingLoan = user.loanApplications.find(loan => loan.status === 'pending');

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-green-50 to-teal-50 p-4 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 bg-gradient-to-br from-green-400/10 via-emerald-400/10 to-teal-400/10 animate-pulse" />
      <div className="absolute top-10 right-10 w-20 h-20 bg-green-400/20 rounded-full blur-xl animate-bounce" />
      <div className="absolute bottom-20 left-10 w-16 h-16 bg-teal-400/20 rounded-full blur-lg animate-pulse" />
      
      <div className="relative z-10 max-w-md mx-auto space-y-4">
        {/* Enhanced Header */}
        <div className="flex items-center justify-between animate-slide-down">
          <Button variant="ghost" size="icon" onClick={onBack} className="hover:bg-white/50 hover:backdrop-blur-sm hover:scale-110 transition-all">
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex items-center space-x-2 p-2 rounded-xl bg-white/70 backdrop-blur-sm shadow-lg">
            <div className="relative">
              <Leaf className="w-6 h-6 text-green-600 animate-pulse" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-ping" />
            </div>
            <span className="text-lg font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">GreenCredit</span>
          </div>
          <div className="w-10" />
        </div>

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
        <Card className={`relative overflow-hidden border-2 ${user.greenScore >= 70 ? 'border-green-300' : 'border-yellow-300'} bg-gradient-to-br from-white/80 to-white/60 backdrop-blur-sm shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105 animate-fade-in`} style={{ animationDelay: '0.2s' }}>
          {/* Glowing Effect */}
          <div className={`absolute inset-0 bg-gradient-to-br ${user.greenScore >= 70 ? 'from-green-400/20 to-emerald-400/20' : 'from-yellow-400/20 to-orange-400/20'} blur-sm`} />
          
          <CardContent className="relative pt-6">
            <div className="text-center space-y-4">
              <div className="relative w-36 h-36 mx-auto">
                {/* Glowing Ring */}
                <div className={`absolute inset-0 rounded-full bg-gradient-to-r ${user.greenScore >= 70 ? 'from-green-400 to-emerald-400' : 'from-yellow-400 to-orange-400'} blur-md opacity-30 animate-pulse`} />
                
                {/* Score Circle with Animation */}
                <div className="relative w-full h-full">
                  <svg className="transform -rotate-90 w-36 h-36">
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
                      className="transition-all duration-1000 ease-out"
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
                      <div className={`text-4xl font-bold ${getScoreColor(user.greenScore)} animate-pulse`}>
                        {user.greenScore}
                      </div>
                      <div className="text-xs text-gray-600 font-medium">GreenScore</div>
                      {user.greenScore >= 70 && (
                        <Star className="w-4 h-4 mx-auto text-yellow-500 animate-bounce" />
                      )}
                    </div>
                  </div>
                </div>
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

        {/* Enhanced Category Tiles */}
        <div className="grid grid-cols-2 gap-3 animate-slide-up" style={{ animationDelay: '0.4s' }}>
          {ecoCategories.map((category, index) => {
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
        <div className="grid grid-cols-2 gap-4 animate-slide-up" style={{ animationDelay: '0.6s' }}>
          <Button 
            onClick={onUploadEvidence}
            className="group relative h-24 bg-gradient-to-br from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold rounded-2xl shadow-xl hover:shadow-2xl transform hover:scale-105 hover:-rotate-1 transition-all duration-300 overflow-hidden"
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
        {(activeLoan || pendingLoan) && (
          <Card className="border-blue-200 bg-blue-50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-blue-800 flex items-center space-x-2">
                {activeLoan ? <CheckCircle className="w-4 h-4" /> : <Clock className="w-4 h-4" />}
                <span>{activeLoan ? 'Active Loan' : 'Loan Application'}</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Amount:</span>
                <span className="font-medium">KES {(activeLoan || pendingLoan)!.amount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Interest Rate:</span>
                <span className="font-medium text-green-600">
                  {(activeLoan || pendingLoan)!.interestRate}% APR
                </span>
              </div>
              <Button 
                onClick={onViewRepayments}
                variant="outline"
                size="sm"
                className="w-full mt-3 border-blue-600 text-blue-600 hover:bg-blue-100"
              >
                {activeLoan ? 'View Repayments' : 'Check Status'}
              </Button>
            </CardContent>
          </Card>
        )}

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
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
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
            <Button className="w-full text-sm bg-gradient-to-r from-yellow-500 to-orange-600 hover:from-yellow-600 hover:to-orange-700 text-white font-bold py-3 rounded-xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200">
              <Target className="w-4 h-4 mr-2" />
              View All Tips
              <Sparkles className="w-4 h-4 ml-2 animate-pulse" />
            </Button>
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
  );
}