import { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { BankUser } from '../BankApp';
import { ArrowLeft, Building2, Shield, Lock } from 'lucide-react';

interface BankLoginProps {
  onLogin: (user: BankUser) => void;
  onBack: () => void;
}

export function BankLogin({ onLogin, onBack }: BankLoginProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Mock user roles for demo
  const demoUsers = {
    underwriter: {
      name: 'Sarah Mwangi',
      role: 'underwriter' as const,
      permissions: ['review_applications', 'approve_loans_under_100k', 'view_portfolio']
    },
    manager: {
      name: 'David Kimani',
      role: 'manager' as const,
      permissions: ['review_applications', 'approve_all_loans', 'view_portfolio', 'manage_users', 'export_reports']
    },
    admin: {
      name: 'Grace Wanjiru',
      role: 'admin' as const,
      permissions: ['full_access', 'system_settings', 'audit_logs', 'manage_users', 'export_reports']
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRole) return;

    setIsLoading(true);
    
    // Simulate authentication
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const userData = demoUsers[selectedRole as keyof typeof demoUsers];
    onLogin(userData);
    
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 p-4">
      <div className="max-w-md mx-auto">
        <div className="flex items-center justify-between mb-6">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex items-center space-x-2">
            <Building2 className="w-6 h-6 text-slate-600" />
            <span className="text-lg font-medium text-slate-800">Bank Portal</span>
          </div>
          <div className="w-10" />
        </div>

        <Card className="border-slate-200">
          <CardHeader className="text-center">
            <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Shield className="w-8 h-8 text-slate-600" />
            </div>
            <CardTitle className="text-slate-800">Secure Login</CardTitle>
            <CardDescription>
              Access the GreenCredit underwriting platform
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="sarah.mwangi@bank.co.ke"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label>Demo Role (Select to continue)</Label>
                <Select value={selectedRole} onValueChange={setSelectedRole}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select your role" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="underwriter">
                      <div className="space-y-1">
                        <div className="font-medium">Loan Underwriter</div>
                        <div className="text-xs text-gray-500">Review and approve small loans</div>
                      </div>
                    </SelectItem>
                    <SelectItem value="manager">
                      <div className="space-y-1">
                        <div className="font-medium">Credit Manager</div>
                        <div className="text-xs text-gray-500">Full loan approval authority</div>
                      </div>
                    </SelectItem>
                    <SelectItem value="admin">
                      <div className="space-y-1">
                        <div className="font-medium">System Administrator</div>
                        <div className="text-xs text-gray-500">Complete system access</div>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {selectedRole && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center space-x-2 mb-2">
                    <Badge variant="outline" className="text-blue-600 border-blue-600">
                      {demoUsers[selectedRole as keyof typeof demoUsers].role.charAt(0).toUpperCase() + 
                       demoUsers[selectedRole as keyof typeof demoUsers].role.slice(1)}
                    </Badge>
                    <span className="text-sm font-medium text-blue-800">
                      {demoUsers[selectedRole as keyof typeof demoUsers].name}
                    </span>
                  </div>
                  <p className="text-xs text-blue-700">
                    Permissions: {demoUsers[selectedRole as keyof typeof demoUsers].permissions.slice(0, 3).join(', ')}
                    {demoUsers[selectedRole as keyof typeof demoUsers].permissions.length > 3 && '...'}
                  </p>
                </div>
              )}

              <Button 
                type="submit" 
                className="w-full bg-slate-800 hover:bg-slate-900 h-12"
                disabled={!selectedRole || isLoading}
              >
                {isLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Authenticating...</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <Lock className="w-4 h-4" />
                    <span>Secure Login</span>
                  </div>
                )}
              </Button>
            </form>

            <div className="mt-6 pt-4 border-t border-gray-200">
              <div className="flex items-center justify-center space-x-2 text-xs text-gray-500">
                <Shield className="w-3 h-3" />
                <span>Multi-factor authentication enabled</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="mt-6 text-center">
          <Badge variant="outline" className="text-xs text-gray-500">
            Demo Version - Real implementation would require proper authentication
          </Badge>
        </div>
      </div>
    </div>
  );
}