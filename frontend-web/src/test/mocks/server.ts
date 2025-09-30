/**
 * Mock server setup using MSW (Mock Service Worker) for testing.
 * Provides mock API responses for all HaliCred backend endpoints.
 */

import { setupServer } from 'msw/node';
import { rest } from 'msw';

// Mock data
const mockUser = {
  id: '1',
  phone: '+254700000001',
  email: 'test@example.com',
  name: 'John Doe',
  business_name: 'Doe Enterprises',
  business_type: 'farmer',
  location: 'Nairobi',
  is_active: true,
  is_verified: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockGreenScore = {
  id: '1',
  user_id: '1',
  overall_score: 75,
  energy_efficiency: 80,
  water_conservation: 70,
  waste_management: 85,
  renewable_energy: 65,
  carbon_footprint: 72,
  confidence_score: 0.85,
  evidence_count: 5,
  last_updated: '2024-01-01T00:00:00Z',
  scoring_factors: {
    led_lighting: { score: 15, weight: 0.2 },
    solar_panels: { score: 20, weight: 0.3 },
    water_recycling: { score: 18, weight: 0.25 },
  },
  recommendations: [
    {
      action: 'Install additional solar panels',
      potential_impact: '+5 score points',
      estimated_cost: 'KES 150,000',
      payback_period: '18 months',
    },
  ],
};

const mockLoanApplication = {
  id: '1',
  user_id: '1',
  amount: 500000,
  term: 12,
  purpose: 'equipment',
  interest_rate: 12.5,
  monthly_payment: 44471.0,
  status: 'pending',
  application_date: '2024-01-01T00:00:00Z',
  last_updated: '2024-01-01T00:00:00Z',
  collateral_description: 'Farm equipment and land title',
  business_plan_summary: 'Expand sustainable farming operations',
  requested_use_of_funds: 'Purchase organic fertilizers and irrigation equipment',
};

const mockEvidence = {
  id: '1',
  user_id: '1',
  evidence_type: 'solar_panel',
  file_path: '/uploads/evidence/solar_panel_receipt.jpg',
  file_name: 'solar_panel_receipt.jpg',
  file_size: 1024000,
  mime_type: 'image/jpeg',
  description: 'Receipt for solar panel installation',
  upload_date: '2024-01-01T00:00:00Z',
  processing_status: 'completed',
  ai_analysis_result: {
    confidence: 0.92,
    extracted_text: 'Solar Panel System - KES 200,000',
    sustainability_impact: 'High - Renewable energy adoption',
    score_contribution: 15,
  },
  verification_status: 'verified',
  verified_date: '2024-01-01T00:00:00Z',
};

// Define request handlers
export const handlers = [
  // Authentication endpoints
  rest.post('/api/auth/otp', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: 'sent',
        message: 'OTP sent successfully',
      })
    );
  }),

  rest.post('/api/auth/verify', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        access_token: 'mock_access_token',
        refresh_token: 'mock_refresh_token',
        token_type: 'bearer',
        expires_in: 3600,
        user: mockUser,
      })
    );
  }),

  rest.post('/api/auth/register', (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        access_token: 'mock_access_token',
        refresh_token: 'mock_refresh_token',
        token_type: 'bearer',
        expires_in: 3600,
        user: mockUser,
      })
    );
  }),

  rest.post('/api/auth/refresh', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        access_token: 'new_mock_access_token',
        refresh_token: 'new_mock_refresh_token',
        token_type: 'bearer',
        expires_in: 3600,
      })
    );
  }),

  rest.post('/api/auth/logout', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: 'logged_out',
        message: 'Successfully logged out',
      })
    );
  }),

  // User endpoints
  rest.get('/api/users/profile', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockUser));
  }),

  rest.put('/api/users/profile', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json({ ...mockUser, ...req.body }));
  }),

  // Green Score endpoints
  rest.get('/api/scores/current', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockGreenScore));
  }),

  rest.get('/api/scores/history', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json([
        { ...mockGreenScore, overall_score: 65, last_updated: '2023-12-01T00:00:00Z' },
        { ...mockGreenScore, overall_score: 70, last_updated: '2023-12-15T00:00:00Z' },
        mockGreenScore,
      ])
    );
  }),

  // Loan endpoints
  rest.post('/api/loans/apply', (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        ...mockLoanApplication,
        application_id: '1',
      })
    );
  }),

  rest.get('/api/loans/my-loans', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json([mockLoanApplication]));
  }),

  rest.get('/api/loans/:id', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockLoanApplication));
  }),

  rest.put('/api/loans/:id', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json({ ...mockLoanApplication, ...req.body }));
  }),

  rest.delete('/api/loans/:id', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ ...mockLoanApplication, status: 'cancelled' })
    );
  }),

  rest.get('/api/loans/eligibility', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        eligible: true,
        max_amount: 1000000,
        min_amount: 50000,
        interest_rate: 12.5,
        max_term: 36,
        factors: ['green_score_bonus', 'verified_profile'],
      })
    );
  }),

  // Evidence endpoints
  rest.post('/api/evidence/upload', (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        evidence_id: '1',
        status: 'uploaded',
        message: 'Evidence uploaded successfully',
      })
    );
  }),

  rest.get('/api/evidence', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json([mockEvidence]));
  }),

  rest.get('/api/evidence/:id', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockEvidence));
  }),

  rest.delete('/api/evidence/:id', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: 'deleted',
        message: 'Evidence deleted successfully',
      })
    );
  }),

  // Health endpoints
  rest.get('/api/health/ready', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: 'healthy',
        timestamp: '2024-01-01T00:00:00Z',
        checks: {
          database: { status: 'healthy', response_time: 45 },
          redis: { status: 'healthy', response_time: 12 },
          external_services: { status: 'healthy', response_time: 234 },
        },
      })
    );
  }),

  rest.get('/api/health/live', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        status: 'alive',
        uptime: 3600,
        timestamp: '2024-01-01T00:00:00Z',
      })
    );
  }),

  // Error handlers for testing error states
  rest.get('/api/error/500', (req, res, ctx) => {
    return res(
      ctx.status(500),
      ctx.json({
        error: {
          category: 'SYSTEM',
          message: 'Internal server error',
          correlation_id: 'test-correlation-id',
        },
      })
    );
  }),

  rest.get('/api/error/404', (req, res, ctx) => {
    return res(
      ctx.status(404),
      ctx.json({
        error: {
          category: 'NOT_FOUND',
          message: 'Resource not found',
          correlation_id: 'test-correlation-id',
        },
      })
    );
  }),

  rest.get('/api/error/401', (req, res, ctx) => {
    return res(
      ctx.status(401),
      ctx.json({
        error: {
          category: 'AUTHENTICATION',
          message: 'Authentication required',
          correlation_id: 'test-correlation-id',
        },
      })
    );
  }),
];

// Create and export the server
export const server = setupServer(...handlers);