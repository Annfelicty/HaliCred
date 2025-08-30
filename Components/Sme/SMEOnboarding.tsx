import { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Checkbox } from '../ui/checkbox';
import { ArrowLeft, Leaf, Tractor, Scissors, Zap, Building, Sparkles, CheckCircle, Shield, Smartphone, MapPin, Camera } from 'lucide-react';

interface SMEOnboardingProps {
  onComplete: (userData: {
    name: string;
    phone: string;
    businessType: 'farmer' | 'salon' | 'welding' | 'other';
    businessName: string;
    location: string;
  }) => void;
  onBack: () => void;
}

export function SMEOnboarding({ onComplete, onBack }: SMEOnboardingProps) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    businessType: '' as 'farmer' | 'salon' | 'welding' | 'other',
    businessName: '',
    location: '',
    consents: {
      mpesa: false,
      geo: false,
      receipts: false
    }
  });

  const businessTypes = [
    { value: 'farmer', label: 'Agriculture/Farming', icon: Tractor, description: 'Crops, livestock, agro-processing' },
    { value: 'salon', label: 'Beauty Salon/Spa', icon: Scissors, description: 'Hair, beauty, wellness services' },
    { value: 'welding', label: 'Welding/Metal Work', icon: Zap, description: 'Fabrication, repair, metalworking' },
    { value: 'other', label: 'Other Business', icon: Building, description: 'General small business' }
  ];

  const handleNext = () => {
    if (step < 3) {
      setStep(step + 1);
    } else {
      onComplete({
        name: formData.name,
        phone: formData.phone,
        businessType: formData.businessType,
        businessName: formData.businessName,
        location: formData.location
      });
    }
  };

  const canProceed = () => {
    switch (step) {
      case 1:
        return formData.name && formData.phone;
      case 2:
        return formData.businessType;
      case 3:
        return formData.businessName && formData.location && Object.values(formData.consents).every(v => v);
      default:
        return false;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-green-50 to-teal-50 p-4 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 bg-gradient-to-br from-green-400/10 via-emerald-400/10 to-teal-400/10 animate-pulse" />
      <div className="absolute top-20 right-10 w-32 h-32 bg-green-400/20 rounded-full blur-2xl animate-bounce" />
      <div className="absolute bottom-20 left-10 w-24 h-24 bg-teal-400/20 rounded-full blur-xl animate-pulse" />
      
      <div className="relative z-10 max-w-md mx-auto">
        {/* Enhanced Header */}
        <div className="flex items-center justify-between mb-8 animate-slide-down">
          <Button variant="ghost" size="icon" onClick={onBack} className="hover:bg-white/50 hover:backdrop-blur-sm hover:scale-110 transition-all">
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex items-center space-x-2 p-3 rounded-2xl bg-white/80 backdrop-blur-sm shadow-lg border border-white/50">
            <div className="relative">
              <Leaf className="w-6 h-6 text-green-600 animate-pulse" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-ping" />
            </div>
            <span className="text-lg font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">GreenCredit</span>
          </div>
          
          {/* Enhanced Progress Indicator */}
          <div className="flex items-center space-x-2">
            <div className="text-sm font-bold text-green-600">{step}/3</div>
            <div className="flex space-x-1">
              {[1, 2, 3].map((stepNum) => (
                <div
                  key={stepNum}
                  className={`w-2 h-2 rounded-full transition-all duration-300 ${
                    stepNum <= step 
                      ? 'bg-gradient-to-r from-green-500 to-emerald-500 scale-125 animate-pulse' 
                      : 'bg-gray-300'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>

        <Card className="bg-white/80 backdrop-blur-sm border-2 border-white/50 shadow-2xl hover:shadow-3xl transition-all duration-500 animate-fade-in">
          {/* Glowing Border Effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-green-400/20 to-emerald-400/20 rounded-xl blur-sm opacity-50" />
          
          <CardHeader className="relative text-center space-y-4">
            {/* Step Icons */}
            <div className="mx-auto w-16 h-16 relative">
              <div className={`absolute inset-0 bg-gradient-to-r ${
                step === 1 ? 'from-green-400 to-emerald-500' :
                step === 2 ? 'from-blue-400 to-cyan-500' :
                'from-purple-400 to-pink-500'
              } rounded-2xl blur-lg opacity-30 animate-pulse`} />
              <div className={`relative w-16 h-16 bg-gradient-to-br ${
                step === 1 ? 'from-green-500 to-emerald-600' :
                step === 2 ? 'from-blue-500 to-cyan-600' :
                'from-purple-500 to-pink-600'
              } rounded-2xl flex items-center justify-center shadow-xl transform hover:scale-110 transition-transform`}>
                {step === 1 && <Sparkles className="w-8 h-8 text-white animate-pulse" />}
                {step === 2 && <Building className="w-8 h-8 text-white" />}
                {step === 3 && <Shield className="w-8 h-8 text-white" />}
              </div>
            </div>
            
            <div className="space-y-2">
              <CardTitle className={`text-2xl font-bold bg-gradient-to-r ${
                step === 1 ? 'from-green-600 to-emerald-600' :
                step === 2 ? 'from-blue-600 to-cyan-600' :
                'from-purple-600 to-pink-600'
              } bg-clip-text text-transparent`}>
                {step === 1 && "Welcome to GreenCredit! 🌱"}
                {step === 2 && "Choose Your Business Type 🏢"}
                {step === 3 && "Almost There! 🎉"}
              </CardTitle>
              <CardDescription className="text-gray-600 font-medium">
                {step === 1 && "Let's start your eco-friendly lending journey"}
                {step === 2 && "This helps us tailor the perfect experience for you"}
                {step === 3 && "Complete your profile and unlock green benefits"}
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="relative space-y-6">
            {step === 1 && (
              <div className="space-y-6 animate-slide-up">
                <div className="space-y-3">
                  <Label htmlFor="name" className="flex items-center space-x-2 font-bold text-gray-700">
                    <Sparkles className="w-4 h-4 text-green-500" />
                    <span>Full Name</span>
                  </Label>
                  <div className="relative">
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="Enter your full name"
                      className="pl-12 h-12 bg-white/80 backdrop-blur-sm border-2 border-green-200 focus:border-green-500 rounded-xl font-medium transition-all hover:bg-white/90"
                    />
                    <div className="absolute left-4 top-1/2 -translate-y-1/2">
                      <div className="w-4 h-4 bg-green-500 rounded-full animate-pulse" />
                    </div>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <Label htmlFor="phone" className="flex items-center space-x-2 font-bold text-gray-700">
                    <Smartphone className="w-4 h-4 text-blue-500" />
                    <span>Phone Number</span>
                  </Label>
                  <div className="relative">
                    <Input
                      id="phone"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      placeholder="+254 700 000 000"
                      className="pl-12 h-12 bg-white/80 backdrop-blur-sm border-2 border-blue-200 focus:border-blue-500 rounded-xl font-medium transition-all hover:bg-white/90"
                    />
                    <div className="absolute left-4 top-1/2 -translate-y-1/2">
                      <div className="w-4 h-4 bg-blue-500 rounded-full animate-pulse" />
                    </div>
                  </div>
                </div>
                
                {/* Encouragement Message */}
                <div className="p-4 bg-gradient-to-r from-green-100/80 to-emerald-100/80 backdrop-blur-sm rounded-xl border border-green-200">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="text-sm font-medium text-green-800">Your journey to better loans starts here! 🚀</span>
                  </div>
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-4 animate-slide-up">
                {businessTypes.map((type, index) => {
                  const Icon = type.icon;
                  const isSelected = formData.businessType === type.value;
                  
                  return (
                    <div
                      key={type.value}
                      className={`group relative overflow-hidden p-5 border-2 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-105 ${
                        isSelected
                          ? 'border-green-500 bg-gradient-to-br from-green-50/80 to-emerald-50/80 shadow-xl'
                          : 'border-gray-200 bg-white/60 hover:border-green-300 hover:bg-white/80'
                      }`}
                      onClick={() => setFormData({ ...formData, businessType: type.value as any })}
                      style={{ animationDelay: `${index * 0.1}s` }}
                    >
                      {/* Selected Indicator */}
                      {isSelected && (
                        <div className="absolute top-3 right-3">
                          <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center animate-bounce">
                            <CheckCircle className="w-4 h-4 text-white" />
                          </div>
                        </div>
                      )}
                      
                      {/* Gradient Background for Selected */}
                      {isSelected && (
                        <div className="absolute inset-0 bg-gradient-to-r from-green-400/10 to-emerald-400/10 animate-pulse" />
                      )}
                      
                      <div className="relative flex items-start space-x-4">
                        <div className={`p-3 rounded-2xl transition-all group-hover:scale-110 ${
                          isSelected 
                            ? 'bg-gradient-to-br from-green-500 to-emerald-600 text-white shadow-lg' 
                            : 'bg-gray-100 text-gray-400 group-hover:bg-green-100 group-hover:text-green-600'
                        }`}>
                          <Icon className="w-7 h-7" />
                        </div>
                        
                        <div className="flex-1 space-y-2">
                          <div className={`font-bold text-lg ${isSelected ? 'text-green-800' : 'text-gray-800'}`}>
                            {type.label}
                          </div>
                          <div className="text-sm text-gray-600 leading-relaxed">
                            {type.description}
                          </div>
                          
                          {/* Benefits Preview */}
                          <div className="flex items-center space-x-2 text-xs">
                            <Sparkles className={`w-3 h-3 ${isSelected ? 'text-green-500' : 'text-gray-400'}`} />
                            <span className={`${isSelected ? 'text-green-600' : 'text-gray-500'}`}>
                              Tailored eco-solutions available
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
                
                {/* Selection Encouragement */}
                <div className="p-4 bg-gradient-to-r from-blue-100/80 to-cyan-100/80 backdrop-blur-sm rounded-xl border border-blue-200 text-center">
                  <div className="flex items-center justify-center space-x-2">
                    <Building className="w-5 h-5 text-blue-600" />
                    <span className="text-sm font-medium text-blue-800">We'll customize your experience based on your business! 🎯</span>
                  </div>
                </div>
              </div>
            )}

            {step === 3 && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="businessName">Business Name</Label>
                  <Input
                    id="businessName"
                    value={formData.businessName}
                    onChange={(e) => setFormData({ ...formData, businessName: e.target.value })}
                    placeholder="Enter your business name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="location">Location (Town/County)</Label>
                  <Input
                    id="location"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    placeholder="e.g., Nakuru, Kenya"
                  />
                </div>
                
                <div className="pt-4 border-t space-y-4">
                  <h4 className="font-medium text-gray-900">Required Permissions</h4>
                  
                  <div className="space-y-3">
                    <div className="flex items-start space-x-3">
                      <Checkbox
                        checked={formData.consents.mpesa}
                        onCheckedChange={(checked) => 
                          setFormData({ 
                            ...formData, 
                            consents: { ...formData.consents, mpesa: checked as boolean } 
                          })
                        }
                      />
                      <div className="space-y-1">
                        <p className="text-sm font-medium">M-Pesa Transaction Access</p>
                        <p className="text-xs text-gray-500">
                          Access transaction history to verify business activity and repayments
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3">
                      <Checkbox
                        checked={formData.consents.geo}
                        onCheckedChange={(checked) => 
                          setFormData({ 
                            ...formData, 
                            consents: { ...formData.consents, geo: checked as boolean } 
                          })
                        }
                      />
                      <div className="space-y-1">
                        <p className="text-sm font-medium">Location Services</p>
                        <p className="text-xs text-gray-500">
                          Verify business location and eco-actions using satellite data
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3">
                      <Checkbox
                        checked={formData.consents.receipts}
                        onCheckedChange={(checked) => 
                          setFormData({ 
                            ...formData, 
                            consents: { ...formData.consents, receipts: checked as boolean } 
                          })
                        }
                      />
                      <div className="space-y-1">
                        <p className="text-sm font-medium">Document Upload</p>
                        <p className="text-xs text-gray-500">
                          Upload receipts and photos to prove eco-friendly investments
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}

            <div className="pt-6">
              <Button 
                onClick={handleNext} 
                className={`w-full h-14 text-lg font-bold rounded-2xl shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-300 ${
                  canProceed() 
                    ? 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white animate-pulse' 
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                } ${step === 3 ? 'hover:rotate-1' : 'hover:-rotate-1'}`}
                disabled={!canProceed()}
              >
                <div className="flex items-center justify-center space-x-3">
                  {step === 3 ? (
                    <>
                      <CheckCircle className="w-6 h-6 animate-bounce" />
                      <span>Complete Setup & Start Earning!</span>
                      <Sparkles className="w-6 h-6 animate-pulse" />
                    </>
                  ) : (
                    <>
                      <span>Continue Journey</span>
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-white rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                        <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                      </div>
                    </>
                  )}
                </div>
              </Button>
            </div>
          </CardContent>
        </Card>
        
        {/* Fun Footer */}
        <div className="mt-6 text-center animate-fade-in" style={{ animationDelay: '0.8s' }}>
          <div className="flex justify-center space-x-4 text-xs text-gray-500 mb-2">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              <span>Secure</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
              <span>Fast</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" />
              <span>Eco-Friendly</span>
            </div>
          </div>
          <p className="text-xs text-gray-400">Join thousands of eco-conscious businesses! 🌱</p>
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