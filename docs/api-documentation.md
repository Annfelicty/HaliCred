# HaliCred API Documentation

## Overview

The HaliCred API is a RESTful service built with FastAPI that provides AI-powered green credit scoring capabilities for SMEs, farmers, and informal workers. The API enables evidence upload, processing, score calculation, and loan management.

**Base URL**: `https://api.halicred.com` (Production) | `http://localhost:8000` (Development)

**API Version**: 1.0.0

## Authentication

All API endpoints require authentication using JWT tokens obtained through the OTP verification process.

### Authentication Flow

1. **Send OTP**: Request an OTP for phone-based authentication
2. **Verify OTP**: Verify the OTP and receive JWT access token
3. **Use Token**: Include token in Authorization header for all subsequent requests

#### Headers
```http
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

## API Endpoints

### Authentication Endpoints

#### Send OTP
```http
POST /auth/otp
```

**Request Body**:
```json
{
  "phone": "+254123456789",
  "user_type": "sme"
}
```

**Response**:
```json
{
  "message": "OTP sent successfully",
  "expires_in": 300,
  "phone": "+254123456789"
}
```

#### Verify OTP
```http
POST /auth/verify
```

**Request Body**:
```json
{
  "phone": "+254123456789",
  "otp": "123456"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_id": "uuid-string",
  "user_type": "sme"
}
```

### User Profile Endpoints

#### Get Current User Profile
```http
GET /me
```

**Response**:
```json
{
  "id": "uuid-string",
  "phone": "+254123456789",
  "user_type": "sme",
  "created_at": "2025-09-30T10:00:00Z",
  "business_profile": {
    "business_name": "Green Farm Ltd",
    "sector": "agriculture",
    "location": "Nairobi, Kenya"
  }
}
```

#### Update User Profile
```http
PUT /me/profile
```

**Request Body**:
```json
{
  "business_name": "Green Farm Ltd",
  "sector": "agriculture",
  "location": "Nairobi, Kenya",
  "business_size": "small",
  "annual_revenue": 1000000
}
```

### Evidence Management Endpoints

#### Create Evidence Upload
```http
POST /evidence/
```

**Response**:
```json
{
  "evidence_id": "uuid-string",
  "upload_url": "https://presigned-s3-url...",
  "expires_at": "2025-09-30T11:00:00Z"
}
```

#### Process Evidence with AI
```http
POST /ai/evidence/process
```

**Request Body** (multipart/form-data):
```
file: <uploaded_file>
sector: "agriculture"
region: "Kenya"
evidence_type: "renewable_energy"
description: "Solar panel installation receipt"
```

**Response**:
```json
{
  "ai_evidence_id": "uuid-string",
  "status": "completed",
  "confidence_score": 0.89,
  "processing_results": {
    "emission_reduction": 2.5,
    "green_score_impact": 15.2,
    "carbon_credits": 0.8
  },
  "ai_insights": {
    "evidence_validity": "high",
    "sustainability_impact": "significant",
    "recommendations": ["Consider expanding solar capacity"]
  }
}
```

#### Get Evidence Details
```http
GET /evidence/{evidence_id}
```

**Response**:
```json
{
  "id": "uuid-string",
  "user_id": "uuid-string",
  "status": "processed",
  "created_at": "2025-09-30T10:00:00Z",
  "file_url": "https://s3-url...",
  "processing_results": {
    "ocr_text": "Solar panel invoice...",
    "ai_analysis": "High-quality renewable energy evidence",
    "emission_reduction": 2.5
  }
}
```

### Green Score Endpoints

#### Compute Green Score
```http
POST /score/compute
```

**Request Body**:
```json
{
  "user_id": "uuid-string",
  "evidence_ids": ["uuid-1", "uuid-2"],
  "sector": "agriculture",
  "region": "Kenya"
}
```

**Response**:
```json
{
  "green_score": 78.5,
  "score_breakdown": {
    "energy_efficiency": 85.0,
    "waste_management": 72.0,
    "sustainable_practices": 80.0,
    "carbon_footprint": 75.0
  },
  "confidence_level": "high",
  "carbon_credits_earned": 12.5,
  "recommendations": [
    "Improve waste segregation practices",
    "Consider biogas installation"
  ]
}
```

#### Get User's Green Score
```http
GET /score/me
```

**Response**:
```json
{
  "current_score": 78.5,
  "score_history": [
    {
      "score": 78.5,
      "date": "2025-09-30T10:00:00Z",
      "evidence_count": 5
    }
  ],
  "ranking": {
    "percentile": 85,
    "sector_average": 65.2
  }
}
```

### Loan Management Endpoints

#### Get Loan Quote
```http
POST /loan/quote
```

**Request Body**:
```json
{
  "amount": 100000,
  "purpose": "equipment_purchase",
  "term_months": 24
}
```

**Response**:
```json
{
  "quote_id": "uuid-string",
  "amount": 100000,
  "term_months": 24,
  "interest_rate": 12.5,
  "monthly_payment": 4708.50,
  "green_discount": 2.5,
  "eligibility_score": 78.5,
  "approved_amount": 100000,
  "conditions": ["Maintain green score above 70"]
}
```

#### Apply for Loan
```http
POST /loan/apply
```

**Request Body**:
```json
{
  "quote_id": "uuid-string",
  "purpose": "Solar panel installation",
  "collateral_type": "equipment",
  "business_plan": "Expand renewable energy capacity..."
}
```

**Response**:
```json
{
  "application_id": "uuid-string",
  "status": "under_review",
  "submitted_at": "2025-09-30T10:00:00Z",
  "expected_decision": "2025-10-05T10:00:00Z"
}
```

### AI Engine Endpoints

#### Health Check
```http
GET /ai/health
```

**Response**:
```json
{
  "status": "healthy",
  "services": {
    "gemini": "connected",
    "google_vision": "connected",
    "climatiq": "connected"
  },
  "timestamp": "2025-09-30T10:00:00Z"
}
```

#### Calculate Emissions
```http
POST /ai/emissions/calculate
```

**Request Body**:
```json
{
  "activity_type": "electricity_consumption",
  "region": "Kenya",
  "amount": 1000,
  "unit": "kWh"
}
```

**Response**:
```json
{
  "emissions_kg_co2": 850.5,
  "activity_id": "electricity_grid_ke",
  "data_version": "2023.1",
  "confidence": "high"
}
```

## Error Handling

The API uses standard HTTP status codes and returns error details in a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid phone number format",
    "details": {
      "field": "phone",
      "provided": "123456789",
      "expected": "+254XXXXXXXXX"
    }
  },
  "timestamp": "2025-09-30T10:00:00Z",
  "request_id": "req-uuid-string"
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Authentication endpoints**: 5 requests per minute per IP
- **Evidence processing**: 10 requests per hour per user
- **General endpoints**: 100 requests per minute per user

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1672531200
```

## Response Formats

All API responses follow a consistent structure:

### Success Response
```json
{
  "data": { ... },
  "timestamp": "2025-09-30T10:00:00Z",
  "request_id": "req-uuid-string"
}
```

### Error Response
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": { ... }
  },
  "timestamp": "2025-09-30T10:00:00Z",
  "request_id": "req-uuid-string"
}
```

## Data Types and Enums

### User Types
- `sme`: Small and Medium Enterprises
- `bank`: Financial institutions
- `admin`: Administrative users

### Sectors
- `agriculture`: Farming and agricultural activities
- `manufacturing`: Manufacturing and production
- `transport`: Transportation services
- `energy`: Energy production and services
- `services`: Service sector businesses

### Evidence Types
- `renewable_energy`: Solar panels, wind turbines, etc.
- `energy_efficiency`: LED lights, efficient appliances
- `waste_management`: Recycling, composting systems
- `sustainable_transport`: Electric vehicles, public transport
- `water_conservation`: Drip irrigation, rainwater harvesting

### Loan Status
- `draft`: Application being prepared
- `submitted`: Application submitted for review
- `under_review`: Being reviewed by bank
- `approved`: Loan approved
- `rejected`: Loan rejected
- `disbursed`: Funds disbursed

## SDKs and Client Libraries

Official SDKs are available for:
- Python: `pip install halicred-sdk`
- JavaScript/Node.js: `npm install halicred-sdk`
- Mobile (React Native): `npm install @halicred/react-native-sdk`

## Testing

### Test Environment
- **Base URL**: `https://api-test.halicred.com`
- **Test Phone**: `+254700000000` (always returns OTP: `123456`)
- **Test API Key**: Contact development team

### Postman Collection
Download the Postman collection for testing: [HaliCred API Collection](./postman/halicred-api.json)

## Support

For API support and questions:
- Documentation: [docs.halicred.com](https://docs.halicred.com)
- Email: api-support@halicred.com
- Issues: [GitHub Issues](https://github.com/Annfelicty/hali-cred/issues)

---

**Last Updated**: September 30, 2025
**API Version**: 1.0.0
**Documentation Version**: 7.0.0