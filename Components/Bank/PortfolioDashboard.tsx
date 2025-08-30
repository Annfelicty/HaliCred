import { useState } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { LoanApplication } from '../BankApp';
import { 
  ArrowLeft, 
  PieChart, 
  TrendingUp, 
  Download, 
  Leaf, 
  DollarSign,
  Users,
  MapPin,
  Droplets,
  Zap,
  BarChart3
} from 'lucide-react';

interface PortfolioDashboardProps {
  applications: LoanApplication[];
  onBack: () => void;
}

export function PortfolioDashboard({ applications, onBack }: PortfolioDashboardProps) {
  const [timeframe, setTimeframe] = useState('month');

  // Calculate portfolio metrics
  const totalLoans = applications.filter(app => app.status === 'approved' || app.status === 'disbursed').length;
  const totalAmount = applications.reduce((sum, app) => 
    app.status === 'approved' || app.status === 'disbursed' ? sum + app.amount : sum, 0
  );
  const avgGreenScore = Math.round(
    applications.reduce((sum, app) => sum + app.greenScore, 0) / applications.length
  );
  const nplRate = 2.3; // Mock NPL rate
  
  // ESG Impact Calculations
  const totalCO2Saved = Math.round(applications.length * 4.5 + Math.random() * 15);
  const totalWaterSaved = Math.round(applications.length * 1200 + Math.random() * 800);
  const totalEnergySaved = Math.round(applications.length * 2100 + Math.random() * 600);
  
  // Business type distribution
  const businessTypeStats = applications.reduce((stats, app) => {
    stats[app.businessType] = (stats[app.businessType] || 0) + 1;
    return stats;
  }, {} as Record<string, number>);
  
  // Geographic distribution (mock data)
  const geographicStats = [
    { region: 'Nairobi', loans: 12, amount: 1200000, co2Saved: 45 },
    { region: 'Nakuru', loans: 8, amount: 850000, co2Saved: 32 },
    { region: 'Eldoret', loans: 6, amount: 720000, co2Saved: 28 },
    { region: 'Thika', loans: 4, amount: 420000, co2Saved: 18 },
    { region: 'Kisumu', loans: 3, amount: 380000, co2Saved: 15 }
  ];

  // Risk distribution
  const riskStats = applications.reduce((stats, app) => {
    stats[app.riskAssessment.fraudRisk] = (stats[app.riskAssessment.fraudRisk] || 0) + 1;
    return stats;
  }, {} as Record<string, number>);

  const greenScoreBands = applications.reduce((bands, app) => {
    if (app.greenScore >= 80) bands.excellent += 1;
    else if (app.greenScore >= 60) bands.good += 1;
    else if (app.greenScore >= 40) bands.fair += 1;
    else bands.poor += 1;
    return bands;
  }, { excellent: 0, good: 0, fair: 0, poor: 0 });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="max-w-6xl mx-auto space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="text-center">
            <h1 className="text-xl font-medium text-slate-800">Portfolio Dashboard</h1>
            <p className="text-sm text-slate-600">ESG Impact & Performance Analytics</p>
          </div>
          <Button variant="outline" size="sm" className="border-slate-300">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center space-y-2">
              <DollarSign className="w-6 h-6 mx-auto text-blue-600" />
              <div className="text-2xl font-bold text-slate-900">KES {(totalAmount / 1000000).toFixed(1)}M</div>
              <div className="text-xs text-slate-600">Total Portfolio</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 text-center space-y-2">
              <Users className="w-6 h-6 mx-auto text-green-600" />
              <div className="text-2xl font-bold text-slate-900">{totalLoans}</div>
              <div className="text-xs text-slate-600">Active Loans</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 text-center space-y-2">
              <TrendingUp className="w-6 h-6 mx-auto text-purple-600" />
              <div className="text-2xl font-bold text-slate-900">{avgGreenScore}</div>
              <div className="text-xs text-slate-600">Avg Green Score</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 text-center space-y-2">
              <BarChart3 className="w-6 h-6 mx-auto text-red-600" />
              <div className="text-2xl font-bold text-slate-900">{nplRate}%</div>
              <div className="text-xs text-slate-600">NPL Rate</div>
            </CardContent>
          </Card>
        </div>

        {/* Main Dashboard */}
        <Tabs defaultValue="impact" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="impact">ESG Impact</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="geographic">Geography</TabsTrigger>
            <TabsTrigger value="risk">Risk Analysis</TabsTrigger>
          </TabsList>

          {/* ESG Impact Tab */}
          <TabsContent value="impact" className="space-y-4">
            <div className="grid lg:grid-cols-2 gap-4">
              <Card className="border-green-200 bg-green-50">
                <CardHeader>
                  <CardTitle className="text-base text-green-800 flex items-center space-x-2">
                    <Leaf className="w-5 h-5" />
                    <span>Environmental Impact</span>
                  </CardTitle>
                  <CardDescription className="text-green-700">
                    Cumulative impact from funded eco-actions
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-3 gap-3">
                    <div className="text-center p-3 bg-white rounded-lg border border-green-200">
                      <div className="text-2xl font-bold text-green-600">{totalCO2Saved}</div>
                      <div className="text-xs text-slate-600">tCO₂ Avoided</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg border border-blue-200">
                      <div className="text-2xl font-bold text-blue-600">{totalWaterSaved}L</div>
                      <div className="text-xs text-slate-600">Water Saved</div>
                    </div>
                    <div className="text-center p-3 bg-white rounded-lg border border-yellow-200">
                      <div className="text-2xl font-bold text-yellow-600">{totalEnergySaved}</div>
                      <div className="text-xs text-slate-600">kWh Saved</div>
                    </div>
                  </div>
                  
                  <div className="p-3 bg-white rounded-lg border border-green-200">
                    <h4 className="font-medium text-green-800 mb-2">Impact by Action Type</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Solar installations:</span>
                        <span className="font-medium">{Math.round(totalCO2Saved * 0.4)} tCO₂</span>
                      </div>
                      <div className="flex justify-between">
                        <span>LED lighting:</span>
                        <span className="font-medium">{Math.round(totalCO2Saved * 0.3)} tCO₂</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Efficient equipment:</span>
                        <span className="font-medium">{Math.round(totalCO2Saved * 0.3)} tCO₂</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">GreenScore Distribution</CardTitle>
                  <CardDescription>Portfolio breakdown by sustainability performance</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {[
                    { label: 'Excellent (80+)', count: greenScoreBands.excellent, color: 'bg-green-600' },
                    { label: 'Good (60-79)', count: greenScoreBands.good, color: 'bg-blue-600' },
                    { label: 'Fair (40-59)', count: greenScoreBands.fair, color: 'bg-yellow-600' },
                    { label: 'Poor (<40)', count: greenScoreBands.poor, color: 'bg-red-600' }
                  ].map((band, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>{band.label}</span>
                        <span className="font-medium">{band.count} loans</span>
                      </div>
                      <Progress 
                        value={(band.count / applications.length) * 100} 
                        className="h-2"
                      />
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Monthly Impact Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-32 flex items-end justify-between space-x-1">
                  {Array.from({ length: 6 }, (_, i) => {
                    const height = Math.random() * 80 + 20;
                    const month = new Date(2024, i, 1).toLocaleString('default', { month: 'short' });
                    return (
                      <div key={i} className="flex flex-col items-center space-y-2 flex-1">
                        <div 
                          className="bg-green-600 rounded-t w-full"
                          style={{ height: `${height}%` }}
                        ></div>
                        <span className="text-xs text-slate-600">{month}</span>
                      </div>
                    );
                  })}
                </div>
                <div className="mt-4 text-center">
                  <p className="text-sm text-slate-600">CO₂ avoided (tCO₂) per month</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Performance Tab */}
          <TabsContent value="performance" className="space-y-4">
            <div className="grid lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Business Type Performance</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {Object.entries(businessTypeStats).map(([type, count]) => (
                    <div key={type} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="capitalize">{type.replace('_', ' ')}</span>
                        <span className="font-medium">{count} loans</span>
                      </div>
                      <Progress value={(count / applications.length) * 100} className="h-2" />
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Risk Profile</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {Object.entries(riskStats).map(([risk, count]) => {
                    const color = risk === 'low' ? 'text-green-600' : 
                                 risk === 'medium' ? 'text-yellow-600' : 'text-red-600';
                    return (
                      <div key={risk} className="flex justify-between items-center">
                        <span className={`text-sm font-medium capitalize ${color}`}>{risk} Risk</span>
                        <Badge variant="outline" className={color}>
                          {count} loans
                        </Badge>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Portfolio Health Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">97.7%</div>
                    <div className="text-sm text-green-700">Repayment Rate</div>
                  </div>
                  <div className="text-center p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">14.2%</div>
                    <div className="text-sm text-blue-700">Avg Interest Rate</div>
                  </div>
                  <div className="text-center p-4 bg-purple-50 border border-purple-200 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">18mo</div>
                    <div className="text-sm text-purple-700">Avg Loan Term</div>
                  </div>
                  <div className="text-center p-4 bg-orange-50 border border-orange-200 rounded-lg">
                    <div className="text-2xl font-bold text-orange-600">KES 89K</div>
                    <div className="text-sm text-orange-700">Avg Loan Size</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Geographic Tab */}
          <TabsContent value="geographic" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center space-x-2">
                  <MapPin className="w-5 h-5" />
                  <span>Regional Distribution</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {geographicStats.map((region, index) => (
                    <div key={index} className="p-4 border border-slate-200 rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-medium">{region.region}</span>
                        <Badge variant="outline">{region.loans} loans</Badge>
                      </div>
                      <div className="grid grid-cols-3 gap-3 text-sm">
                        <div>
                          <p className="text-slate-600">Amount</p>
                          <p className="font-medium">KES {(region.amount / 1000).toFixed(0)}K</p>
                        </div>
                        <div>
                          <p className="text-slate-600">CO₂ Saved</p>
                          <p className="font-medium text-green-600">{region.co2Saved} tCO₂</p>
                        </div>
                        <div>
                          <p className="text-slate-600">Avg Size</p>
                          <p className="font-medium">KES {(region.amount / region.loans / 1000).toFixed(0)}K</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Risk Analysis Tab */}
          <TabsContent value="risk" className="space-y-4">
            <div className="grid lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Risk Concentration</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span>Single borrower limit</span>
                        <span className="text-green-600">✓ Compliant</span>
                      </div>
                      <Progress value={75} className="h-2" />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span>Sector concentration</span>
                        <span className="text-green-600">✓ Diversified</span>
                      </div>
                      <Progress value={65} className="h-2" />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span>Geographic spread</span>
                        <span className="text-green-600">✓ Well spread</span>
                      </div>
                      <Progress value={80} className="h-2" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Early Warning Indicators</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded">
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                        <span className="text-sm">Repayment performance</span>
                      </div>
                      <span className="text-sm text-green-600">Normal</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded">
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                        <span className="text-sm">GreenScore trends</span>
                      </div>
                      <span className="text-sm text-green-600">Improving</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded">
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-yellow-600 rounded-full"></div>
                        <span className="text-sm">Market conditions</span>
                      </div>
                      <span className="text-sm text-yellow-600">Monitor</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">ESG Risk Assessment</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="text-xl font-bold text-green-600">Low</div>
                    <div className="text-sm text-green-700">Environmental Risk</div>
                    <div className="text-xs text-slate-600 mt-1">Climate resilience high</div>
                  </div>
                  <div className="text-center p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="text-xl font-bold text-blue-600">Low</div>
                    <div className="text-sm text-blue-700">Social Risk</div>
                    <div className="text-xs text-slate-600 mt-1">Community impact positive</div>
                  </div>
                  <div className="text-center p-4 bg-purple-50 border border-purple-200 rounded-lg">
                    <div className="text-xl font-bold text-purple-600">Medium</div>
                    <div className="text-sm text-purple-700">Governance Risk</div>
                    <div className="text-xs text-slate-600 mt-1">SME governance standards</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}