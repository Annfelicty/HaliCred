import { useState, useEffect } from 'react';
import { SMEApp } from './Components/SMEApp';
import { BankApp } from './Components/BankApp';
import { Button } from './Components/Ui/button';
import { Badge } from './Components/Ui/badge';
import { Leaf, Building2, Sparkles, TrendingUp, Star, Zap } from 'lucide-react';

export default function App() {
  const [userType, setUserType] = useState<'sme' | 'bank' | null>(null);
  const [particles, setParticles] = useState<Array<{id: number, x: number, y: number, delay: number}>>([]);

  useEffect(() => {
    // Generate floating particles
    const newParticles = Array.from({ length: 20 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      delay: Math.random() * 4
    }));
    setParticles(newParticles);
  }, []);

  if (userType === 'sme') {
    return <SMEApp onBack={() => setUserType(null)} />;
  }

  if (userType === 'bank') {
    return <BankApp onBack={() => setUserType(null)} />;
  }

  return (
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50">
      {/* Animated Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-green-400/10 via-teal-400/10 to-emerald-400/10 animate-pulse" />
      
      {/* Floating Particles */}
      {particles.map((particle) => (
        <div
          key={particle.id}
          className="absolute w-1 h-1 bg-green-400/30 rounded-full animate-bounce"
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
            animationDelay: `${particle.delay}s`,
            animationDuration: '3s'
          }}
        />
      ))}

      {/* Glowing Orbs */}
      <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-green-400/20 rounded-full blur-xl animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-24 h-24 bg-teal-400/20 rounded-full blur-xl animate-pulse" style={{ animationDelay: '1s' }} />
      <div className="absolute top-1/2 right-1/3 w-16 h-16 bg-emerald-400/20 rounded-full blur-lg animate-pulse" style={{ animationDelay: '2s' }} />

      <div className="relative z-10 min-h-screen flex items-center justify-center p-4">
        <div className="max-w-md w-full space-y-8 text-center">
          {/* Hero Section */}
          <div className="space-y-6 animate-fade-in">
            {/* Logo with Glow Effect */}
            <div className="relative mx-auto w-24 h-24 group">
              <div className="absolute inset-0 bg-gradient-to-r from-green-500 to-emerald-500 rounded-3xl blur-lg opacity-75 group-hover:opacity-100 transition-opacity animate-pulse" />
              <div className="relative w-24 h-24 bg-gradient-to-br from-green-500 to-emerald-600 rounded-3xl flex items-center justify-center shadow-2xl transform transition-transform hover:scale-110 hover:rotate-3">
                <Leaf className="w-12 h-12 text-white animate-pulse" />
                <div className="absolute -top-1 -right-1">
                  <Star className="w-6 h-6 text-yellow-400 animate-spin" style={{ animationDuration: '3s' }} />
                </div>
              </div>
            </div>

            {/* Title with Gradient Text */}
            <div className="space-y-3">
              <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 bg-clip-text text-transparent animate-pulse">
                GreenCredit Score
              </h1>
              <div className="flex items-center justify-center space-x-2">
                <Sparkles className="w-5 h-5 text-yellow-500 animate-bounce" />
                <p className="text-gray-600 font-medium">Eco-friendly actions unlock better loans</p>
                <Sparkles className="w-5 h-5 text-yellow-500 animate-bounce" style={{ animationDelay: '0.5s' }} />
              </div>
              
              {/* Achievement Badge */}
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-gradient-to-r from-yellow-100 to-orange-100 border border-yellow-200">
                <TrendingUp className="w-4 h-4 text-orange-500" />
                <span className="text-xs font-medium text-orange-700">Impact-driven lending</span>
                <Zap className="w-4 h-4 text-yellow-500 animate-pulse" />
              </div>
            </div>
          </div>

          {/* Interactive Cards */}
          <div className="space-y-4 animate-slide-up" style={{ animationDelay: '0.3s' }}>
            {/* SME Card */}
            <div className="group relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-green-500/20 to-emerald-500/20 rounded-2xl blur-sm opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative p-6 bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-green-100/50 space-y-4 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 hover:bg-white/90">
                <div className="flex items-center justify-center space-x-3">
                  <div className="p-2 bg-gradient-to-br from-green-100 to-emerald-100 rounded-xl group-hover:scale-110 transition-transform">
                    <Leaf className="w-6 h-6 text-green-600 group-hover:animate-pulse" />
                  </div>
                  <h2 className="text-xl font-bold text-gray-900">SME / Borrower</h2>
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                    <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                    <div className="w-2 h-2 bg-teal-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
                  </div>
                </div>
                <p className="text-gray-600 leading-relaxed">
                  For farmers, salons, welding shops and other small businesses
                </p>
                <div className="flex items-center justify-center space-x-2 text-xs text-green-600 mb-2">
                  <Star className="w-3 h-3 fill-current" />
                  <span>Get better rates with eco-actions</span>
                  <Star className="w-3 h-3 fill-current" />
                </div>
                <Button 
                  onClick={() => setUserType('sme')} 
                  className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-semibold py-3 rounded-xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 hover:rotate-1"
                >
                  <Sparkles className="w-4 h-4 mr-2 animate-pulse" />
                  Start Your Green Journey
                  <TrendingUp className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>

            {/* Bank Card */}
            <div className="group relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-teal-500/20 to-cyan-500/20 rounded-2xl blur-sm opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative p-6 bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-teal-100/50 space-y-4 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 hover:bg-white/90">
                <div className="flex items-center justify-center space-x-3">
                  <div className="p-2 bg-gradient-to-br from-teal-100 to-cyan-100 rounded-xl group-hover:scale-110 transition-transform">
                    <Building2 className="w-6 h-6 text-teal-600 group-hover:animate-pulse" />
                  </div>
                  <h2 className="text-xl font-bold text-gray-900">Bank / Underwriter</h2>
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-teal-400 rounded-full animate-pulse" />
                    <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
                  </div>
                </div>
                <p className="text-gray-600 leading-relaxed">
                  Review applications and manage loan portfolio
                </p>
                <div className="flex items-center justify-center space-x-2 text-xs text-teal-600 mb-2">
                  <Star className="w-3 h-3 fill-current" />
                  <span>ESG-powered underwriting</span>
                  <Star className="w-3 h-3 fill-current" />
                </div>
                <Button 
                  onClick={() => setUserType('bank')} 
                  variant="outline"
                  className="w-full border-2 border-teal-500 text-teal-600 hover:bg-gradient-to-r hover:from-teal-500 hover:to-cyan-600 hover:text-white font-semibold py-3 rounded-xl hover:shadow-xl transform hover:scale-105 transition-all duration-200 hover:-rotate-1"
                >
                  <Building2 className="w-4 h-4 mr-2" />
                  Access Admin Portal
                  <Zap className="w-4 h-4 ml-2 animate-pulse" />
                </Button>
              </div>
            </div>
          </div>

          {/* Enhanced Footer */}
          <div className="pt-6 space-y-3 animate-fade-in" style={{ animationDelay: '0.6s' }}>
            <div className="flex justify-center space-x-6 text-xs text-gray-500">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span>Eco-Verified</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                <span>AI-Powered</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" />
                <span>Secure</span>
              </div>
            </div>
            <Badge variant="outline" className="text-xs text-gray-500 border-gray-300/50 bg-white/50 backdrop-blur-sm">
              Demo Version - Real implementation would require authentication
            </Badge>
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
        
        .animate-fade-in {
          animation: fade-in 0.8s ease-out forwards;
        }
        
        .animate-slide-up {
          animation: slide-up 0.8s ease-out forwards;
        }
      `}</style>
    </div>
  );
}