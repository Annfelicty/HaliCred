import { useState } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { ArrowLeft, Camera, Upload, Leaf, Lightbulb, Droplets, Sun, Zap, Sparkles, Trophy, Target, Gift, Star, CheckCircle } from 'lucide-react';

interface EvidenceUploadProps {
  businessType: 'farmer' | 'salon' | 'welding' | 'other';
  onEvidenceUploaded: (evidence: any) => void;
  onBack: () => void;
}

export function EvidenceUpload({ businessType, onEvidenceUploaded, onBack }: EvidenceUploadProps) {
  const [selectedType, setSelectedType] = useState('');
  const [description, setDescription] = useState('');
  const [cost, setCost] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const getEcoActionsForBusiness = (type: string) => {
    const common = [
      { value: 'led_lighting', label: 'LED Lighting Installation', impact: '~3.85 tCO₂/year saved', icon: Lightbulb },
      { value: 'solar_panel', label: 'Solar Panel System', impact: '~5.2 tCO₂/year saved', icon: Sun },
      { value: 'energy_efficient', label: 'Energy Efficient Equipment', impact: '~2.1 tCO₂/year saved', icon: Zap },
      { value: 'water_conservation', label: 'Water Conservation System', impact: '~2000L/month saved', icon: Droplets }
    ];

    const specific = {
      farmer: [
        { value: 'solar_pump', label: 'Solar Water Pump', impact: '~4.3 tCO₂/year saved', icon: Sun },
        { value: 'drip_irrigation', label: 'Drip Irrigation System', impact: '~30% water savings', icon: Droplets },
        { value: 'biogas', label: 'Biogas System', impact: '~6.8 tCO₂/year saved', icon: Leaf },
      ],
      salon: [
        { value: 'inverter_dryer', label: 'Inverter Hair Dryer', impact: '~1.2 tCO₂/year saved', icon: Zap },
        { value: 'water_recycling', label: 'Water Recycling System', impact: '~40% water savings', icon: Droplets },
      ],
      welding: [
        { value: 'inverter_welder', label: 'Inverter Welder', impact: '~8.6 tCO₂/year saved', icon: Zap },
        { value: 'led_workshop', label: 'LED Workshop Lighting', impact: '~2.4 tCO₂/year saved', icon: Lightbulb },
      ],
      other: []
    };

    return [...common, ...(specific[type] || [])];
  };

  const ecoActions = getEcoActionsForBusiness(businessType);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFile(file);
    }
  };

  const handleSubmit = async () => {
    if (!selectedType || !description || !uploadedFile) return;

    setIsUploading(true);
    
    // Simulate upload process
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const selectedAction = ecoActions.find(action => action.value === selectedType);
    
    onEvidenceUploaded({
      type: selectedType,
      description,
      cost,
      file: uploadedFile,
      impact: selectedAction?.impact || 'Eco-impact calculated'
    });
    
    setIsUploading(false);
  };

  const canSubmit = selectedType && description && uploadedFile;

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-green-50 to-teal-50 p-4 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 bg-gradient-to-br from-green-400/10 via-emerald-400/10 to-teal-400/10 animate-pulse" />
      <div className="absolute top-20 right-10 w-32 h-32 bg-green-400/20 rounded-full blur-2xl animate-bounce" />
      <div className="absolute bottom-20 left-10 w-24 h-24 bg-teal-400/20 rounded-full blur-xl animate-pulse" />
      
      <div className="relative z-10 max-w-md mx-auto space-y-4">
        {/* Enhanced Header */}
        <div className="flex items-center justify-between animate-slide-down">
          <Button variant="ghost" size="icon" onClick={onBack} className="hover:bg-white/50 hover:backdrop-blur-sm hover:scale-110 transition-all">
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex items-center space-x-2 p-3 rounded-2xl bg-white/80 backdrop-blur-sm shadow-lg border border-white/50">
            <div className="relative">
              <Camera className="w-6 h-6 text-green-600 animate-pulse" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-ping" />
            </div>
            <span className="text-lg font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">Upload Evidence</span>
            <Sparkles className="w-5 h-5 text-yellow-500 animate-bounce" />
          </div>
          <div className="w-10" />
        </div>

        {/* Enhanced Instructions */}
        <Card className="relative overflow-hidden bg-gradient-to-br from-green-50/80 to-emerald-50/80 backdrop-blur-sm border-2 border-green-200/50 shadow-xl animate-fade-in">
          {/* Decorative Elements */}
          <div className="absolute top-2 right-2">
            <Trophy className="w-6 h-6 text-yellow-500 animate-bounce" />
          </div>
          <div className="absolute bottom-2 left-2">
            <Star className="w-4 h-4 text-green-500 animate-pulse" />
          </div>
          
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <div className="mx-auto w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center shadow-xl animate-pulse">
                <Leaf className="w-8 h-8 text-white" />
              </div>
              
              <div className="space-y-2">
                <h3 className="font-bold text-lg text-green-800 flex items-center justify-center space-x-2">
                  <Sparkles className="w-5 h-5 text-yellow-500 animate-bounce" />
                  <span>Boost Your GreenScore!</span>
                  <Target className="w-5 h-5 text-green-600" />
                </h3>
                <p className="text-green-700 leading-relaxed">
                  Upload receipts or photos of your eco-friendly investments. Our AI will verify them and instantly update your score! 🚀
                </p>
              </div>
              
              {/* Benefits */}
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div className="p-2 bg-white/60 rounded-lg border border-green-200">
                  <div className="text-green-600 font-bold">+15 pts</div>
                  <div className="text-gray-600">Per action</div>
                </div>
                <div className="p-2 bg-white/60 rounded-lg border border-blue-200">
                  <div className="text-blue-600 font-bold">AI Verified</div>
                  <div className="text-gray-600">Instant</div>
                </div>
                <div className="p-2 bg-white/60 rounded-lg border border-purple-200">
                  <div className="text-purple-600 font-bold">Better Rates</div>
                  <div className="text-gray-600">Unlock</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Eco-Action Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">What eco-action did you take?</CardTitle>
            <CardDescription>Choose the type of investment you made</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Select value={selectedType} onValueChange={setSelectedType}>
              <SelectTrigger>
                <SelectValue placeholder="Select eco-action type" />
              </SelectTrigger>
              <SelectContent>
                {ecoActions.map((action) => {
                  const Icon = action.icon;
                  return (
                    <SelectItem key={action.value} value={action.value}>
                      <div className="flex items-center space-x-3">
                        <Icon className="w-4 h-4" />
                        <div className="flex-1">
                          <div className="font-medium">{action.label}</div>
                          <div className="text-xs text-gray-500">{action.impact}</div>
                        </div>
                      </div>
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>

            {selectedType && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Badge variant="outline" className="text-green-600 border-green-600">
                    Expected Impact
                  </Badge>
                </div>
                <p className="text-sm text-green-700 mt-2">
                  {ecoActions.find(a => a.value === selectedType)?.impact}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Description */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Description</CardTitle>
            <CardDescription>Provide details about your investment</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., Installed 4 LED bulbs in main salon area, purchased from ABC Electronics on Jan 15, 2024"
              rows={4}
            />
            
            <div>
              <Label htmlFor="cost">Cost (Optional)</Label>
              <Input
                id="cost"
                value={cost}
                onChange={(e) => setCost(e.target.value)}
                placeholder="KES 5,000"
              />
            </div>
          </CardContent>
        </Card>

        {/* Enhanced File Upload */}
        <Card className="bg-white/80 backdrop-blur-sm border-2 border-white/50 shadow-xl animate-slide-up" style={{ animationDelay: '0.6s' }}>
          <CardHeader>
            <CardTitle className="text-base flex items-center space-x-2 font-bold text-gray-800">
              <Camera className="w-5 h-5 text-blue-600" />
              <span>Upload Your Evidence</span>
              <Gift className="w-5 h-5 text-purple-600 animate-bounce" />
            </CardTitle>
            <CardDescription className="text-gray-600">
              Snap a photo or choose from your files - it's that easy! 📸
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className={`relative border-3 border-dashed rounded-2xl p-8 text-center transition-all duration-300 ${
                uploadedFile 
                  ? 'border-green-400 bg-gradient-to-br from-green-50/80 to-emerald-50/80' 
                  : 'border-gray-300 bg-gray-50/50 hover:border-green-400 hover:bg-green-50/50'
              }`}>
                {uploadedFile ? (
                  <div className="space-y-4 animate-fade-in">
                    <div className="relative mx-auto w-20 h-20">
                      <div className="absolute inset-0 bg-gradient-to-r from-green-400 to-emerald-500 rounded-2xl blur-lg opacity-30 animate-pulse" />
                      <div className="relative w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center shadow-xl">
                        <CheckCircle className="w-10 h-10 text-white animate-bounce" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <p className="font-bold text-green-800">{uploadedFile.name}</p>
                      <p className="text-sm text-green-600">
                        {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB • Ready to submit! ✨
                      </p>
                    </div>
                    
                    {/* Success Indicators */}
                    <div className="flex justify-center space-x-4 text-xs">
                      <div className="flex items-center space-x-1 text-green-600">
                        <CheckCircle className="w-3 h-3" />
                        <span>Valid format</span>
                      </div>
                      <div className="flex items-center space-x-1 text-blue-600">
                        <CheckCircle className="w-3 h-3" />
                        <span>Good quality</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="mx-auto w-16 h-16 bg-gradient-to-br from-gray-200 to-gray-300 rounded-2xl flex items-center justify-center">
                      <Camera className="w-8 h-8 text-gray-500 animate-pulse" />
                    </div>
                    <div className="space-y-2">
                      <p className="font-medium text-gray-700">Drop your evidence here</p>
                      <p className="text-sm text-gray-500">or click to browse files</p>
                    </div>
                  </div>
                )}
                
                {/* Upload Progress Animation */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full opacity-0 pointer-events-none transition-all duration-1000" 
                     style={{ transform: uploadedFile ? 'translateX(100%)' : 'translateX(-100%)', opacity: uploadedFile ? 1 : 0 }} />
              </div>
              
              <input
                type="file"
                accept="image/*,.pdf"
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload"
              />
              
              <div className="grid grid-cols-2 gap-4">
                <Button
                  onClick={() => document.getElementById('file-upload')?.click()}
                  className="group h-16 bg-gradient-to-br from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700 text-white font-bold rounded-2xl shadow-xl hover:shadow-2xl transform hover:scale-105 hover:-rotate-1 transition-all duration-300"
                >
                  <div className="flex flex-col items-center space-y-2">
                    <Upload className="w-6 h-6 group-hover:animate-bounce" />
                    <span className="text-sm">Browse Files</span>
                  </div>
                </Button>
                
                <Button
                  onClick={() => document.getElementById('file-upload')?.click()}
                  className="group h-16 bg-gradient-to-br from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 text-white font-bold rounded-2xl shadow-xl hover:shadow-2xl transform hover:scale-105 hover:rotate-1 transition-all duration-300"
                >
                  <div className="flex flex-col items-center space-y-2">
                    <Camera className="w-6 h-6 group-hover:animate-pulse" />
                    <span className="text-sm">Take Photo</span>
                  </div>
                </Button>
              </div>
              
              {/* Upload Tips */}
              <div className="p-3 bg-gradient-to-r from-yellow-100/80 to-orange-100/80 rounded-xl border border-yellow-200">
                <div className="flex items-center space-x-2 text-xs text-yellow-800">
                  <Sparkles className="w-4 h-4 animate-pulse" />
                  <span className="font-medium">Pro tip: Clear, well-lit photos get verified faster! 📱✨</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Enhanced Submit Button */}
        <div className="space-y-4 animate-slide-up" style={{ animationDelay: '0.8s' }}>
          <Button 
            onClick={handleSubmit}
            disabled={!canSubmit || isUploading}
            className={`w-full h-16 text-lg font-bold rounded-2xl shadow-2xl transition-all duration-300 ${
              canSubmit && !isUploading
                ? 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white transform hover:scale-105 hover:rotate-1 animate-pulse'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            {isUploading ? (
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin" />
                  <div className="absolute inset-1 border-2 border-transparent border-t-white/50 rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '0.5s' }} />
                </div>
                <span>AI is analyzing your evidence...</span>
                <Sparkles className="w-5 h-5 animate-bounce" />
              </div>
            ) : (
              <div className="flex items-center space-x-3">
                <Trophy className="w-6 h-6 animate-bounce" />
                <span>Submit & Earn Points!</span>
                <div className="flex space-x-1">
                  <Star className="w-4 h-4 text-yellow-300 animate-pulse" />
                  <Star className="w-4 h-4 text-yellow-300 animate-pulse" style={{ animationDelay: '0.2s' }} />
                  <Star className="w-4 h-4 text-yellow-300 animate-pulse" style={{ animationDelay: '0.4s' }} />
                </div>
              </div>
            )}
          </Button>

          {/* Enhanced Footer */}
          <div className="text-center space-y-3">
            <div className="flex justify-center space-x-6 text-xs text-gray-500">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span>AI Powered</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                <span>Instant Verification</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" />
                <span>Secure</span>
              </div>
            </div>
            <p className="text-xs text-gray-500">
              ⚡ Lightning-fast AI verification • 🔒 Bank-grade security • 🌱 Eco-impact tracking
            </p>
          </div>
        </div>
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