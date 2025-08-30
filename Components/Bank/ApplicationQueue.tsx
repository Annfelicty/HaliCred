import { useState } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Input } from '../ui/input';
import { LoanApplication } from '../BankApp';
import { 
  ArrowLeft, 
  Search, 
  Filter, 
  Eye, 
  Clock, 
  AlertTriangle, 
  CheckCircle,
  TrendingUp,
  MapPin,
  DollarSign,
  Calendar
} from 'lucide-react';

interface ApplicationQueueProps {
  applications: LoanApplication[];
  onReviewApplication: (application: LoanApplication) => void;
  onBack: () => void;
}

export function ApplicationQueue({ applications, onReviewApplication, onBack }: ApplicationQueueProps) {
  const [sortBy, setSortBy] = useState('greenScore');
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Filter and sort applications
  const filteredApps = applications
    .filter(app => {
      const matchesStatus = filterStatus === 'all' || app.status === filterStatus;
      const matchesSearch = searchQuery === '' || 
        app.applicantName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        app.businessName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        app.location.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesStatus && matchesSearch;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'greenScore':
          return b.greenScore - a.greenScore;
        case 'amount':
          return b.amount - a.amount;
        case 'date':
          return new Date(b.appliedDate).getTime() - new Date(a.appliedDate).getTime();
        case 'risk':
          const riskOrder = { low: 1, medium: 2, high: 3 };
          return riskOrder[b.riskAssessment.fraudRisk] - riskOrder[a.riskAssessment.fraudRisk];
        default:
          return 0;
      }
    });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4" />;
      case 'under_review':
        return <Eye className="w-4 h-4" />;
      case 'approved':
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-600';
      case 'under_review':
        return 'bg-blue-600';
      case 'approved':
        return 'bg-green-600';
      case 'rejected':
        return 'bg-red-600';
      default:
        return 'bg-gray-600';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getGreenScoreColor = (score: number) => {
    if (score >= 70) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="max-w-6xl mx-auto space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="text-center">
            <h1 className="text-xl font-medium text-slate-800">Application Queue</h1>
            <p className="text-sm text-slate-600">{filteredApps.length} applications to review</p>
          </div>
          <div className="w-10" />
        </div>

        {/* Filters and Search */}
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Search</label>
                <div className="relative">
                  <Search className="absolute left-3 top-3 w-4 h-4 text-slate-400" />
                  <Input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Name, business, location..."
                    className="pl-10"
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Status</label>
                <Select value={filterStatus} onValueChange={setFilterStatus}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="under_review">Under Review</SelectItem>
                    <SelectItem value="approved">Approved</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">Sort By</label>
                <Select value={sortBy} onValueChange={setSortBy}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="greenScore">Green Score</SelectItem>
                    <SelectItem value="amount">Loan Amount</SelectItem>
                    <SelectItem value="date">Application Date</SelectItem>
                    <SelectItem value="risk">Risk Level</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="flex items-end">
                <Button variant="outline" className="w-full border-slate-300">
                  <Filter className="w-4 h-4 mr-2" />
                  Advanced
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Application List */}
        <div className="space-y-3">
          {filteredApps.map((app) => (
            <Card key={app.id} className="border-slate-200 hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1 space-y-3">
                    {/* Header Row */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div>
                          <div className="font-medium text-slate-900">{app.applicantName}</div>
                          <div className="text-sm text-slate-600">{app.businessName}</div>
                        </div>
                        <Badge className={getStatusColor(app.status)}>
                          <div className="flex items-center space-x-1">
                            {getStatusIcon(app.status)}
                            <span className="text-xs">
                              {app.status.replace('_', ' ').charAt(0).toUpperCase() + app.status.replace('_', ' ').slice(1)}
                            </span>
                          </div>
                        </Badge>
                      </div>
                      
                      <div className="text-right">
                        <div className="text-lg font-bold text-slate-900">
                          KES {app.amount.toLocaleString()}
                        </div>
                        <div className="text-sm text-slate-600">{app.term} months @ {app.interestRate}%</div>
                      </div>
                    </div>

                    {/* Metrics Row */}
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div className="space-y-1">
                        <div className="text-xs text-slate-500 uppercase tracking-wider">Green Score</div>
                        <div className={`text-lg font-bold ${getGreenScoreColor(app.greenScore)}`}>
                          {app.greenScore}
                        </div>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="text-xs text-slate-500 uppercase tracking-wider">Business Type</div>
                        <div className="text-sm capitalize">{app.businessType.replace('_', ' ')}</div>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="text-xs text-slate-500 uppercase tracking-wider">Location</div>
                        <div className="text-sm flex items-center">
                          <MapPin className="w-3 h-3 mr-1" />
                          {app.location.split(',')[0]}
                        </div>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="text-xs text-slate-500 uppercase tracking-wider">Risk Level</div>
                        <Badge variant="outline" className={`text-xs ${getRiskColor(app.riskAssessment.fraudRisk)}`}>
                          {app.riskAssessment.fraudRisk.charAt(0).toUpperCase() + app.riskAssessment.fraudRisk.slice(1)}
                        </Badge>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="text-xs text-slate-500 uppercase tracking-wider">Applied</div>
                        <div className="text-sm flex items-center">
                          <Calendar className="w-3 h-3 mr-1" />
                          {new Date(app.appliedDate).toLocaleDateString('en-GB', { 
                            day: 'numeric', 
                            month: 'short' 
                          })}
                        </div>
                      </div>
                    </div>

                    {/* Risk Alerts */}
                    {app.riskAssessment.anomalies.length > 0 && (
                      <div className="p-2 bg-yellow-50 border border-yellow-200 rounded flex items-start space-x-2">
                        <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="text-xs font-medium text-yellow-800">Risk Alerts</div>
                          <div className="text-xs text-yellow-700">
                            {app.riskAssessment.anomalies[0]}
                            {app.riskAssessment.anomalies.length > 1 && (
                              <span> (+{app.riskAssessment.anomalies.length - 1} more)</span>
                            )}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Eco Actions Preview */}
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center space-x-4 text-slate-600">
                        <span>
                          {app.ecoActions.length} eco-action{app.ecoActions.length !== 1 ? 's' : ''}
                        </span>
                        <span>
                          {app.ecoActions.filter(action => action.verified).length} verified
                        </span>
                        <span>Purpose: {app.purpose.replace('_', ' ')}</span>
                      </div>
                      
                      <Button 
                        onClick={() => onReviewApplication(app)}
                        size="sm"
                        className="bg-slate-800 hover:bg-slate-900"
                      >
                        <Eye className="w-4 h-4 mr-2" />
                        Review
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredApps.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Search className="w-8 h-8 text-slate-400" />
              </div>
              <h3 className="text-lg font-medium text-slate-900 mb-2">No applications found</h3>
              <p className="text-slate-600">Try adjusting your search or filter criteria</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}