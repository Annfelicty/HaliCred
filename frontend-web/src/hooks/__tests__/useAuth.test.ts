/**
 * Comprehensive tests for useAuth hook.
 * Tests authentication state management, login/logout functionality, and token handling.
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import useAuth from '../useAuth';

// Mock the API
jest.mock('../../lib/api');
const mockApi = require('../../lib/api');

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

describe('useAuth Hook', () => {
  let queryClient: QueryClient;
  let wrapper: React.FC<{ children: React.ReactNode }>;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, staleTime: 0, cacheTime: 0 },
      },
    });

    wrapper = ({ children }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );

    jest.clearAllMocks();

    // Mock API responses
    mockApi.sendOTP = jest.fn().mockResolvedValue({
      status: 'sent',
      message: 'OTP sent successfully',
    });

    mockApi.verifyOTP = jest.fn().mockResolvedValue({
      access_token: 'mock_access_token',
      refresh_token: 'mock_refresh_token',
      token_type: 'bearer',
      expires_in: 3600,
      user: {
        id: '1',
        phone: '+254700000001',
        email: 'test@example.com',
        name: 'John Doe',
        business_name: 'Doe Enterprises',
      },
    });

    mockApi.refreshToken = jest.fn().mockResolvedValue({
      access_token: 'new_access_token',
      refresh_token: 'new_refresh_token',
      expires_in: 3600,
    });

    mockApi.logout = jest.fn().mockResolvedValue({
      status: 'logged_out',
    });
  });

  describe('Initial State', () => {
    it('initializes with default unauthenticated state', () => {
      mockLocalStorage.getItem.mockReturnValue(null);

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();
      expect(result.current.isLoading).toBe(false);
    });

    it('initializes with stored authentication data', () => {
      const mockUser = {
        id: '1',
        name: 'John Doe',
        email: 'test@example.com',
      };

      mockLocalStorage.getItem
        .mockReturnValueOnce('stored_access_token')
        .mockReturnValueOnce('stored_refresh_token')
        .mockReturnValueOnce(JSON.stringify(mockUser));

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.token).toBe('stored_access_token');
    });

    it('clears invalid stored data', () => {
      mockLocalStorage.getItem
        .mockReturnValueOnce('invalid_token')
        .mockReturnValueOnce(null)
        .mockReturnValueOnce('invalid_json');

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isAuthenticated).toBe(false);
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('auth_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('user_data');
    });
  });

  describe('OTP Operations', () => {
    it('sends OTP successfully', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.sendOTP('+254700000001');
      });

      expect(mockApi.sendOTP).toHaveBeenCalledWith('+254700000001');
      expect(result.current.otpSent).toBe(true);
    });

    it('handles OTP sending errors', async () => {
      mockApi.sendOTP.mockRejectedValue(new Error('Invalid phone number'));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await expect(
        act(async () => {
          await result.current.sendOTP('invalid_phone');
        })
      ).rejects.toThrow('Invalid phone number');

      expect(result.current.otpSent).toBe(false);
    });

    it('verifies OTP and sets authentication state', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.verifyOTP('+254700000001', '123456');
      });

      expect(mockApi.verifyOTP).toHaveBeenCalledWith('+254700000001', '123456');
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(
        expect.objectContaining({
          id: '1',
          name: 'John Doe',
        })
      );
      expect(result.current.token).toBe('mock_access_token');

      // Check localStorage calls
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('auth_token', 'mock_access_token');
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('refresh_token', 'mock_refresh_token');
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'user_data',
        expect.stringContaining('"id":"1"')
      );
    });

    it('handles OTP verification errors', async () => {
      mockApi.verifyOTP.mockRejectedValue(new Error('Invalid OTP'));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await expect(
        act(async () => {
          await result.current.verifyOTP('+254700000001', '000000');
        })
      ).rejects.toThrow('Invalid OTP');

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });
  });

  describe('Registration', () => {
    it('registers new user successfully', async () => {
      mockApi.register = jest.fn().mockResolvedValue({
        access_token: 'new_user_token',
        refresh_token: 'new_user_refresh',
        user: {
          id: '2',
          phone: '+254700000002',
          name: 'Jane Doe',
          business_name: 'Jane Enterprises',
        },
      });

      const { result } = renderHook(() => useAuth(), { wrapper });

      const registrationData = {
        phone: '+254700000002',
        otp: '123456',
        name: 'Jane Doe',
        email: 'jane@example.com',
        business_name: 'Jane Enterprises',
        business_type: 'salon',
        location: 'Mombasa',
      };

      await act(async () => {
        await result.current.register(registrationData);
      });

      expect(mockApi.register).toHaveBeenCalledWith(registrationData);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user.name).toBe('Jane Doe');
    });

    it('handles registration errors', async () => {
      mockApi.register = jest.fn().mockRejectedValue(
        new Error('Phone number already registered')
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      const registrationData = {
        phone: '+254700000001',
        otp: '123456',
        name: 'Duplicate User',
      };

      await expect(
        act(async () => {
          await result.current.register(registrationData);
        })
      ).rejects.toThrow('Phone number already registered');

      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('Token Management', () => {
    it('refreshes token automatically', async () => {
      mockLocalStorage.getItem
        .mockReturnValueOnce('expired_token')
        .mockReturnValueOnce('valid_refresh_token')
        .mockReturnValueOnce(JSON.stringify({ id: '1', name: 'John' }));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.refreshAuthToken();
      });

      expect(mockApi.refreshToken).toHaveBeenCalledWith('valid_refresh_token');
      expect(result.current.token).toBe('new_access_token');
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('auth_token', 'new_access_token');
    });

    it('handles refresh token expiration', async () => {
      mockApi.refreshToken.mockRejectedValue(new Error('Refresh token expired'));

      mockLocalStorage.getItem
        .mockReturnValueOnce('expired_token')
        .mockReturnValueOnce('expired_refresh_token')
        .mockReturnValueOnce(JSON.stringify({ id: '1' }));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        try {
          await result.current.refreshAuthToken();
        } catch (error) {
          // Expected to fail
        }
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('auth_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('refresh_token');
    });

    it('validates token format', () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      // Mock invalid token
      act(() => {
        result.current.setToken('invalid.token.format');
      });

      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('Logout', () => {
    it('logs out successfully', async () => {
      // Setup authenticated state
      mockLocalStorage.getItem
        .mockReturnValueOnce('valid_token')
        .mockReturnValueOnce('valid_refresh')
        .mockReturnValueOnce(JSON.stringify({ id: '1', name: 'John' }));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.logout();
      });

      expect(mockApi.logout).toHaveBeenCalled();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.token).toBeNull();

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('auth_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('user_data');
    });

    it('handles logout errors gracefully', async () => {
      mockApi.logout.mockRejectedValue(new Error('Server error'));

      mockLocalStorage.getItem
        .mockReturnValueOnce('valid_token')
        .mockReturnValueOnce('valid_refresh')
        .mockReturnValueOnce(JSON.stringify({ id: '1' }));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.logout();
      });

      // Should still clear local state even if API call fails
      expect(result.current.isAuthenticated).toBe(false);
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('auth_token');
    });
  });

  describe('Loading States', () => {
    it('sets loading state during authentication operations', async () => {
      let resolveOTP: (value: any) => void;
      mockApi.verifyOTP.mockReturnValue(
        new Promise((resolve) => {
          resolveOTP = resolve;
        })
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      act(() => {
        result.current.verifyOTP('+254700000001', '123456');
      });

      expect(result.current.isLoading).toBe(true);

      await act(async () => {
        resolveOTP({
          access_token: 'token',
          user: { id: '1', name: 'John' },
        });
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });

    it('clears loading state on error', async () => {
      mockApi.verifyOTP.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        try {
          await result.current.verifyOTP('+254700000001', '123456');
        } catch (error) {
          // Expected error
        }
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('Error Handling', () => {
    it('provides error information', async () => {
      const errorMessage = 'Authentication failed';
      mockApi.verifyOTP.mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        try {
          await result.current.verifyOTP('+254700000001', '123456');
        } catch (error) {
          // Expected error
        }
      });

      expect(result.current.error).toBe(errorMessage);
    });

    it('clears errors on successful operations', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      // Set error state
      await act(async () => {
        try {
          await result.current.verifyOTP('+254700000001', '000000');
        } catch (error) {
          // Expected error
        }
      });

      expect(result.current.error).toBeTruthy();

      // Successful operation should clear error
      await act(async () => {
        await result.current.verifyOTP('+254700000001', '123456');
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('Auto Token Refresh', () => {
    it('automatically refreshes token before expiration', async () => {
      jest.useFakeTimers();

      // Mock token that expires in 5 minutes
      const mockToken = 'header.' + btoa(JSON.stringify({
        exp: Math.floor(Date.now() / 1000) + 300, // 5 minutes from now
      })) + '.signature';

      mockLocalStorage.getItem
        .mockReturnValueOnce(mockToken)
        .mockReturnValueOnce('valid_refresh')
        .mockReturnValueOnce(JSON.stringify({ id: '1' }));

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Fast-forward to 1 minute before expiration
      act(() => {
        jest.advanceTimersByTime(4 * 60 * 1000); // 4 minutes
      });

      await waitFor(() => {
        expect(mockApi.refreshToken).toHaveBeenCalled();
      });

      jest.useRealTimers();
    });
  });

  describe('Persistence', () => {
    it('persists authentication state across browser sessions', () => {
      const userData = { id: '1', name: 'John Doe' };

      mockLocalStorage.getItem
        .mockReturnValueOnce('persistent_token')
        .mockReturnValueOnce('persistent_refresh')
        .mockReturnValueOnce(JSON.stringify(userData));

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(userData);
      expect(result.current.token).toBe('persistent_token');
    });

    it('handles corrupted localStorage data', () => {
      mockLocalStorage.getItem
        .mockReturnValueOnce('invalid_token')
        .mockReturnValueOnce('invalid_refresh')
        .mockReturnValueOnce('invalid_json_data');

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(mockLocalStorage.removeItem).toHaveBeenCalledTimes(3);
    });
  });
});