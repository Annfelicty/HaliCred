import { useState } from 'react';
import { Button } from '../Ui/button';
import { Input } from '../Ui/input';
import { Label } from '../Ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../Ui/card';
import { Alert, AlertDescription } from '../Ui/alert';
import { InputOTP, InputOTPGroup, InputOTPSlot, InputOTPSeparator } from '../Ui/input-otp';
import { Loader2, Mail, Phone, CheckCircle2, AlertCircle } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface OTPLoginProps {
  onLoginSuccess: (token: string, user: any) => void;
  userType?: 'borrower' | 'underwriter';
}

export function OTPLogin({ onLoginSuccess, userType = 'borrower' }: OTPLoginProps) {
  // Set contact type based on user type: borrowers use phone (SMS), underwriters use email
  const defaultContactType = userType === 'underwriter' ? 'email' : 'phone';
  const [contactType, setContactType] = useState<'phone' | 'email'>(defaultContactType);
  const [identifier, setIdentifier] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [fullName, setFullName] = useState('');
  const [step, setStep] = useState<'input' | 'verify'>('input');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [countdown, setCountdown] = useState(0);

  // Start countdown timer
  const startCountdown = () => {
    setCountdown(300); // 5 minutes
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSendOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsLoading(true);

    try {
      const payload = contactType === 'phone'
        ? { phone: identifier }
        : { email: identifier };

      const response = await axios.post(`${API_BASE_URL}/auth/otp`, payload);

      setSuccess(`OTP sent successfully to your ${contactType}`);
      setStep('verify');
      startCountdown();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send OTP. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const payload: any = {
        code: otpCode,
        full_name: fullName || undefined,
      };

      if (contactType === 'phone') {
        payload.phone = identifier;
      } else {
        payload.email = identifier;
      }

      // Set roles based on user type
      if (userType === 'underwriter') {
        payload.roles = ['underwriter'];
      } else {
        payload.roles = ['borrower'];
      }

      const response = await axios.post(`${API_BASE_URL}/auth/verify`, payload);

      const { access_token, user } = response.data;

      setSuccess('Login successful!');
      setTimeout(() => {
        onLoginSuccess(access_token, user);
      }, 1000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid OTP code. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setOtpCode('');
    await handleSendOTP({ preventDefault: () => {} } as React.FormEvent);
  };

  const handleBack = () => {
    setStep('input');
    setOtpCode('');
    setError('');
    setSuccess('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-purple-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-xl border-0">
        <CardHeader className="space-y-1 pb-6">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-blue-500 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-2xl">HC</span>
            </div>
          </div>
          <CardTitle className="text-2xl text-center font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
            Welcome to HaliCred
          </CardTitle>
          <CardDescription className="text-center">
            {step === 'input'
              ? 'Enter your phone number or email to get started'
              : 'Enter the verification code we sent you'
            }
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Error Alert */}
          {error && (
            <Alert variant="destructive" className="animate-in fade-in-50">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Success Alert */}
          {success && (
            <Alert className="border-green-200 bg-green-50 text-green-800 animate-in fade-in-50">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <AlertDescription>{success}</AlertDescription>
            </Alert>
          )}

          {step === 'input' ? (
            <form onSubmit={handleSendOTP} className="space-y-4">
              {/* Contact Type Input - Auto-selected based on userType */}
              {contactType === 'phone' ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                    <Phone className="w-4 h-4" />
                    <span>Phone Verification (SMS)</span>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone Number</Label>
                    <Input
                      id="phone"
                      type="tel"
                      placeholder="+254712345678"
                      value={identifier}
                      onChange={(e) => setIdentifier(e.target.value)}
                      required
                      className="text-lg"
                    />
                    <p className="text-xs text-muted-foreground">
                      Include country code (e.g., +254 for Kenya)
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                    <Mail className="w-4 h-4" />
                    <span>Email Verification</span>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="you@example.com"
                      value={identifier}
                      onChange={(e) => setIdentifier(e.target.value)}
                      required
                      className="text-lg"
                    />
                  </div>
                </div>
              )}

              <Button
                type="submit"
                className="w-full h-12 text-base bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700"
                disabled={isLoading || !identifier}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Sending OTP...
                  </>
                ) : (
                  'Send Verification Code'
                )}
              </Button>

              <p className="text-xs text-center text-muted-foreground">
                By continuing, you agree to HaliCred's Terms of Service and Privacy Policy
              </p>
            </form>
          ) : (
            <form onSubmit={handleVerifyOTP} className="space-y-6">
              {/* OTP Input */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-center block">Verification Code</Label>
                  <div className="flex justify-center">
                    <InputOTP
                      maxLength={6}
                      value={otpCode}
                      onChange={setOtpCode}
                    >
                      <InputOTPGroup>
                        <InputOTPSlot index={0} />
                        <InputOTPSlot index={1} />
                        <InputOTPSlot index={2} />
                      </InputOTPGroup>
                      <InputOTPSeparator />
                      <InputOTPGroup>
                        <InputOTPSlot index={3} />
                        <InputOTPSlot index={4} />
                        <InputOTPSlot index={5} />
                      </InputOTPGroup>
                    </InputOTP>
                  </div>
                  <p className="text-xs text-center text-muted-foreground">
                    Code sent to {contactType === 'phone' ? identifier : identifier}
                  </p>
                </div>

                {/* Countdown Timer */}
                {countdown > 0 && (
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground">
                      Code expires in <span className="font-mono font-semibold text-orange-600">{formatTime(countdown)}</span>
                    </p>
                  </div>
                )}

                {/* Full Name (Optional for new users) */}
                <div className="space-y-2">
                  <Label htmlFor="fullName">Full Name (Optional)</Label>
                  <Input
                    id="fullName"
                    type="text"
                    placeholder="John Doe"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Required for new accounts only
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-3">
                <Button
                  type="submit"
                  className="w-full h-12 text-base bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700"
                  disabled={isLoading || otpCode.length !== 6}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Verifying...
                    </>
                  ) : (
                    'Verify & Continue'
                  )}
                </Button>

                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    className="flex-1"
                    onClick={handleBack}
                    disabled={isLoading}
                  >
                    Back
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="flex-1"
                    onClick={handleResendOTP}
                    disabled={isLoading || countdown > 240}
                  >
                    Resend Code
                  </Button>
                </div>
              </div>

              <p className="text-xs text-center text-muted-foreground">
                Didn't receive the code? Check your spam folder or try resending after {countdown > 240 ? formatTime(countdown - 240) : '0:00'}
              </p>
            </form>
          )}

          {/* User Type Badge */}
          <div className="pt-4 border-t">
            <div className="flex items-center justify-center gap-2">
              <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                userType === 'underwriter'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-green-100 text-green-700'
              }`}>
                {userType === 'underwriter' ? '🏦 Bank Portal' : '🌱 Borrower Portal'}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
