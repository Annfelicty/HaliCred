/**
 * Authentication Hook
 * Manages user authentication state and operations
 */
import React, { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import { auth, User, OTPResponse, AuthSuccessResponse } from '../lib/api';

type OtpStage = 'idle' | 'code_sent' | 'verifying';
type ContactType = 'phone' | 'email';

interface AuthContact {
  type: ContactType;
  value: string;
}

interface VerifyParams {
  code: string;
  fullName?: string;
  password?: string;
  roles?: string[];
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  otpStage: OtpStage;
  contact: AuthContact | null;
  lastOtpVerifiedAt: string | null;
  requestOtp: (contact: AuthContact) => Promise<OTPResponse | void>;
  verifyOtp: (params: VerifyParams) => Promise<AuthSuccessResponse | void>;
  loginWithPassword: (password: string, contactOverride?: AuthContact) => Promise<AuthSuccessResponse | void>;
  setContact: (contact: AuthContact | null) => void;
  canLoginWithPassword: (contactType?: ContactType) => boolean;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const CONTACT_STORAGE_KEY = 'auth_contact';
const LAST_OTP_STORAGE_KEY = 'last_otp_verified_at';
const SME_GRACE_MS = 6 * 60 * 60 * 1000;
const BANK_GRACE_MS = 12 * 60 * 60 * 1000;

const getGraceForType = (type: ContactType) => (type === 'email' ? BANK_GRACE_MS : SME_GRACE_MS);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [otpStage, setOtpStage] = useState<OtpStage>('idle');
  const [contact, setContactState] = useState<AuthContact | null>(null);
  const [lastOtpVerifiedAt, setLastOtpVerifiedAtState] = useState<string | null>(null);

  useEffect(() => {
    // Check for existing token on app load
    const token = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('user');
    const savedContactRaw = localStorage.getItem(CONTACT_STORAGE_KEY);
    const savedLastOtp = localStorage.getItem(LAST_OTP_STORAGE_KEY);
    
    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
        // Verify token is still valid
        auth.getCurrentUser()
          .then(userData => {
            setUser(userData);
            localStorage.setItem('user', JSON.stringify(userData));
          })
          .catch(() => {
            // Token invalid, clear storage
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            setUser(null);
          });
      } catch (error) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        setUser(null);
      }
    }

    if (savedContactRaw) {
      try {
        const parsed = JSON.parse(savedContactRaw) as AuthContact;
        setContactState(parsed);
      } catch (error) {
        localStorage.removeItem(CONTACT_STORAGE_KEY);
      }
    }

    if (savedLastOtp) {
      setLastOtpVerifiedAtState(savedLastOtp);
    }
    setLoading(false);
  }, []);

  const storeContact = (nextContact: AuthContact | null) => {
    setContactState(nextContact);
    if (nextContact) {
      localStorage.setItem(CONTACT_STORAGE_KEY, JSON.stringify(nextContact));
    } else {
      localStorage.removeItem(CONTACT_STORAGE_KEY);
    }
  };

  const storeLastOtpVerifiedAt = (timestamp: string | null) => {
    setLastOtpVerifiedAtState(timestamp);
    if (timestamp) {
      localStorage.setItem(LAST_OTP_STORAGE_KEY, timestamp);
    } else {
      localStorage.removeItem(LAST_OTP_STORAGE_KEY);
    }
  };

  const requestOtp = async (nextContact: AuthContact) => {
    try {
      setLoading(true);
      storeContact(nextContact);
      await auth.requestOtp(
        nextContact.type === 'phone'
          ? { phone: nextContact.value }
          : { email: nextContact.value }
      );
      setOtpStage('code_sent');
    } catch (error) {
      console.error('OTP request failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const verifyOtp = async ({ code, fullName, password, roles }: VerifyParams) => {
    try {
      if (!contact) {
        throw new Error('Contact is required before verifying OTP');
      }
      setLoading(true);
      setOtpStage('verifying');

      const response = await auth.verifyOtp({
        ...(contact.type === 'phone' ? { phone: contact.value } : { email: contact.value }),
        code,
        full_name: fullName,
        password,
        roles,
      });

      const { access_token, user: userInfo, last_otp_verified_at } = response;

      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(userInfo));
      setUser(userInfo);
      storeLastOtpVerifiedAt(last_otp_verified_at || new Date().toISOString());
      setOtpStage('idle');
      return response;
    } catch (error) {
      console.error('OTP verification failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const loginWithPassword = async (password: string, contactOverride?: AuthContact) => {
    try {
      setLoading(true);
      const targetContact = contactOverride || contact;
      if (!targetContact) {
        throw new Error('Contact is required before password login');
      }

      storeContact(targetContact);
      const response = await auth.loginWithPassword({
        ...(targetContact.type === 'phone'
          ? { phone: targetContact.value }
          : { email: targetContact.value }),
        password,
      });

      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
      if (response.last_otp_verified_at) {
        storeLastOtpVerifiedAt(response.last_otp_verified_at);
      }
      setUser(response.user);
      setOtpStage('idle');
      return response;
    } catch (error) {
      console.error('Password login failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const canLoginWithPassword = (contactType?: ContactType) => {
    const type = contactType || contact?.type;
    if (!type || !lastOtpVerifiedAt) {
      return false;
    }
    const gracePeriod = getGraceForType(type);
    const lastVerifiedTime = new Date(lastOtpVerifiedAt).getTime();
    if (Number.isNaN(lastVerifiedTime)) {
      return false;
    }
    return Date.now() - lastVerifiedTime <= gracePeriod;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    localStorage.removeItem(CONTACT_STORAGE_KEY);
    localStorage.removeItem(LAST_OTP_STORAGE_KEY);
    setUser(null);
    setOtpStage('idle');
    setContactState(null);
    setLastOtpVerifiedAtState(null);
  };

  const value = {
    user,
    loading,
    otpStage,
    contact,
    lastOtpVerifiedAt,
    requestOtp,
    verifyOtp,
    loginWithPassword,
    setContact: storeContact,
    canLoginWithPassword,
    logout,
    isAuthenticated: !!user,
  };

  return React.createElement(AuthContext.Provider, { value }, children);
};
