import { useState } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Textarea } from '../ui/textarea';
import { LoanApplication } from '../BankApp';
import { 
  ArrowLeft, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  FileText, 
  Image, 
  MapPin, 
  Satellite,
  Eye,
  Camera,
  Shield,
  TrendingUp,
  DollarSign
} from 'lucide-react';

interface CaseReviewProps {
  application: LoanApplication;
  onBack: () => void;
  onDecision: (decision: { action: 'approve' | 'reject' | 'request_more_info'; comment: string; conditions?: string[] }) => void;
}

export function CaseReview({ application, onBack, onDecision }: CaseReviewProps) {
  const [decision, setDecision] = useState<'approve' | 'reject' | 'request_more_info' | ''>('');
  const [comment, setComment] = useState('');
  const [selectedEvidence, setSelectedEvidence] = useState<string | null>(null);

  const handleSubmitDecision = () => {
    if (!decision || !comment) return;
    
    onDecision({
      action: decision as 'approve' | 'reject' | 'request_more_info',
      comment,
      conditions: decision === 'approve' ? ['Regular GreenScore updates required', 'Monthly compliance check'] : undefined
    });
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
      <div className="max-w-4xl mx-auto space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="text-center">
            <h1 className="text-xl font-medium text-slate-800">Case Review</h1>
            <p className="text-sm text-slate-600">Application ID: {application.id}</p>
          </div>
          <Badge variant="outline" className="text-slate-600">
            {new Date(application.appliedDate).toLocaleDateString()}
          </Badge>
        </div>

        {/* Application Summary */}
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>{application.applicantName}</span>
              <div className="flex items-center space-x-2">
                <Badge className={`text-lg px-3 py-1 ${getGreenScoreColor(application.greenScore)}`} variant="outline">
                  {application.greenScore}
                </Badge>
                <span className="text-sm text-slate-600">GreenScore</span>
              </div>
            </CardTitle>
            <CardDescription>{application.businessName} • {application.location}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-slate-600">Loan Amount</p>
                <p className="text-xl font-bold">KES {application.amount.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm text-slate-600">Interest Rate</p>
                <p className="text-xl font-bold text-green-600">{application.interestRate}%</p>
              </div>
              <div>
                <p className="text-sm text-slate-600">Term</p>
                <p className="text-xl font-bold">{application.term} months</p>
              </div>
              <div>
                <p className="text-sm text-slate-600">Purpose</p>
                <p className="text-base font-medium capitalize">{application.purpose.replace('_', ' ')}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tabs for detailed review */}
        <Tabs defaultValue="evidence" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="evidence">Evidence</TabsTrigger>
            <TabsTrigger value="risk">Risk Assessment</TabsTrigger>
            <TabsTrigger value="satellite">Satellite Data</TabsTrigger>
            <TabsTrigger value="decision">Decision</TabsTrigger>
          </TabsList>

          {/* Evidence Tab */}
          <TabsContent value="evidence" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center space-x-2">
                  <Camera className="w-5 h-5" />
                  <span>Uploaded Evidence</span>
                </CardTitle>
                <CardDescription>
                  {application.ecoActions.length} eco-action{application.ecoActions.length !== 1 ? 's' : ''} submitted
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {application.ecoActions.map((action, index) => (
                  <div key={action.id} className="border border-slate-200 rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        <div className="font-medium">{action.description}</div>
                        <div className="text-sm text-slate-600 capitalize">
                          {action.type.replace('_', ' ')}
                        </div>
                      </div>
                      <Badge variant={action.verified ? 'default' : 'secondary'} className={action.verified ? 'bg-green-600' : ''}>
                        {action.verified ? 'Verified' : 'Pending'}
                      </Badge>
                    </div>

                    {/* OCR Results */}
                    {action.ocrResult && (
                      <div className="p-3 bg-blue-50 border border-blue-200 rounded">
                        <div className="flex items-center space-x-2 mb-2">
                          <FileText className="w-4 h-4 text-blue-600" />
                          <span className="text-sm font-medium text-blue-800">OCR Analysis</span>
                        </div>
                        <p className="text-sm text-blue-700 font-mono">{action.ocrResult}</p>
                      </div>
                    )}

                    {/* Risk Flags */}
                    {action.riskFlags && action.riskFlags.length > 0 && (
                      <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
                        <div className="flex items-center space-x-2 mb-2">
                          <AlertTriangle className="w-4 h-4 text-yellow-600" />
                          <span className="text-sm font-medium text-yellow-800">Risk Flags</span>
                        </div>
                        <ul className="text-sm text-yellow-700 space-y-1">
                          {action.riskFlags.map((flag, flagIndex) => (
                            <li key={flagIndex}>• {flag}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Evidence Preview */}
                    <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                      <span className="text-sm text-slate-600">Evidence: {action.evidence}</span>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => setSelectedEvidence(action.evidence)}
                      >
                        <Eye className="w-4 h-4 mr-2" />
                        View
                      </Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Risk Assessment Tab */}
          <TabsContent value="risk" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center space-x-2">
                  <Shield className="w-5 h-5" />
                  <span>Risk Assessment</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-slate-600">Credit Score</p>
                      <p className="text-2xl font-bold text-green-600">{application.riskAssessment.creditScore}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600">Fraud Risk Level</p>
                      <Badge variant="outline" className={`text-sm ${getRiskColor(application.riskAssessment.fraudRisk)}`}>
                        {application.riskAssessment.fraudRisk.charAt(0).toUpperCase() + application.riskAssessment.fraudRisk.slice(1)}
                      </Badge>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-slate-600">Business Type Risk</p>
                      <p className="text-sm">
                        {application.businessType === 'farmer' ? 'Medium' : 
                         application.businessType === 'salon' ? 'Low' : 
                         application.businessType === 'welding' ? 'Medium' : 'Medium'} Risk Profile
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600">Amount vs Income</p>
                      <p className="text-sm text-green-600">Within acceptable range</p>
                    </div>
                  </div>
                </div>

                {/* Anomalies */}
                {application.riskAssessment.anomalies.length > 0 && (
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-center space-x-2 mb-3">
                      <AlertTriangle className="w-5 h-5 text-yellow-600" />
                      <span className="font-medium text-yellow-800">Detected Anomalies</span>
                    </div>
                    <ul className="space-y-2">
                      {application.riskAssessment.anomalies.map((anomaly, index) => (
                        <li key={index} className="text-sm text-yellow-700 flex items-start">
                          <span className="w-2 h-2 bg-yellow-600 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                          {anomaly}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center space-x-2 mb-2">
                    <TrendingUp className="w-5 h-5 text-green-600" />
                    <span className="font-medium text-green-800">Positive Indicators</span>
                  </div>
                  <ul className="space-y-1 text-sm text-green-700">
                    <li>• High GreenScore indicates eco-conscious behavior</li>
                    <li>• {application.ecoActions.filter(a => a.verified).length} verified eco-investments</li>
                    <li>• Credit score above threshold</li>
                    <li>• Consistent business location verification</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Satellite Data Tab */}
          <TabsContent value="satellite" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center space-x-2">
                  <Satellite className="w-5 h-5" />
                  <span>Satellite & Geospatial Analysis</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {application.riskAssessment.satelliteData ? (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center p-4 bg-green-50 border border-green-200 rounded-lg">
                        <div className="text-2xl font-bold text-green-600">{application.riskAssessment.satelliteData.ndvi}</div>
                        <div className="text-sm text-green-700">NDVI Index</div>
                        <div className="text-xs text-gray-600 mt-1">Vegetation health indicator</div>
                      </div>
                      <div className="text-center p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="text-sm font-bold text-blue-600">{application.riskAssessment.satelliteData.landUse}</div>
                        <div className="text-xs text-blue-700">Land Use Classification</div>
                      </div>
                      <div className="text-center p-4 bg-purple-50 border border-purple-200 rounded-lg">
                        <div className="text-sm font-bold text-purple-600 capitalize">
                          {application.riskAssessment.satelliteData.verification}
                        </div>
                        <div className="text-xs text-purple-700">Location Verification</div>
                      </div>
                    </div>

                    <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
                      <div className="flex items-center space-x-2 mb-3">
                        <MapPin className="w-5 h-5 text-slate-600" />
                        <span className="font-medium">Location Analysis</span>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-slate-600">Coordinates Verified:</p>
                          <p className="font-medium">✓ Business location confirmed</p>
                        </div>
                        <div>
                          <p className="text-slate-600">Historical Data:</p>
                          <p className="font-medium">✓ Consistent 6-month presence</p>
                        </div>
                        <div>
                          <p className="text-slate-600">Environmental Context:</p>
                          <p className="font-medium">Suitable for {application.businessType} operations</p>
                        </div>
                        <div>
                          <p className="text-slate-600">Risk Indicators:</p>
                          <p className="font-medium text-green-600">No geographic red flags</p>
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Satellite className="w-8 h-8 text-slate-400" />
                    </div>
                    <p className="text-slate-600">Satellite data not available for this location</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Decision Tab */}
          <TabsContent value="decision" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Make Decision</CardTitle>
                <CardDescription>Review all evidence and make your underwriting decision</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <Button
                    variant={decision === 'approve' ? 'default' : 'outline'}
                    className={`h-20 flex-col space-y-2 ${decision === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'border-green-600 text-green-600 hover:bg-green-50'}`}
                    onClick={() => setDecision('approve')}
                  >
                    <CheckCircle className="w-6 h-6" />
                    <span>Approve</span>
                  </Button>
                  
                  <Button
                    variant={decision === 'reject' ? 'default' : 'outline'}
                    className={`h-20 flex-col space-y-2 ${decision === 'reject' ? 'bg-red-600 hover:bg-red-700' : 'border-red-600 text-red-600 hover:bg-red-50'}`}
                    onClick={() => setDecision('reject')}
                  >
                    <XCircle className="w-6 h-6" />
                    <span>Reject</span>
                  </Button>
                  
                  <Button
                    variant={decision === 'request_more_info' ? 'default' : 'outline'}
                    className={`h-20 flex-col space-y-2 ${decision === 'request_more_info' ? 'bg-yellow-600 hover:bg-yellow-700' : 'border-yellow-600 text-yellow-600 hover:bg-yellow-50'}`}
                    onClick={() => setDecision('request_more_info')}
                  >
                    <FileText className="w-6 h-6" />
                    <span>More Info</span>
                  </Button>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Decision Comments</label>
                  <Textarea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Provide detailed reasoning for your decision..."
                    rows={4}
                  />
                </div>

                {decision === 'approve' && (
                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="space-y-2">
                      <p className="font-medium text-green-800">Loan Conditions:</p>
                      <ul className="text-sm text-green-700 space-y-1">
                        <li>• Regular GreenScore updates required</li>
                        <li>• Monthly eco-impact compliance check</li>
                        <li>• Interest rate subject to GreenScore maintenance</li>
                      </ul>
                    </div>
                  </div>
                )}

                <Button 
                  onClick={handleSubmitDecision}
                  disabled={!decision || !comment}
                  className="w-full bg-slate-800 hover:bg-slate-900 h-12"
                >
                  Submit Decision
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}