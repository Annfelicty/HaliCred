# HaliCred OTP Authentication - Quick Start Guide

**Date:** October 1, 2025
**Status:** ✅ IMPLEMENTED & READY FOR TESTING

---

## Overview

The OTP (One-Time Password) authentication system has been fully implemented with:
- ✅ Africa's Talking SMS integration (Development & Production modes)
- ✅ SMTP Email integration
- ✅ Terminal-only mode for testing
- ✅ Frontend UI components (React/TypeScript)
- ✅ Startup validation checks
- ✅ Health monitoring endpoints

---

## Configuration Modes

### Three Operating Modes

1. **Terminal Mode** (`OTP_MODE=off`)
   - OTP codes printed to backend console
   - No SMS/Email delivery
   - Best for: Local development & debugging

2. **Development Mode** (`OTP_MODE=on`, `ENVIRONMENT_MODE=development`)
   - Uses Africa's Talking **Sandbox**
   - Test phone numbers only
   - Best for: Testing with real API without cost

3. **Production Mode** (`OTP_MODE=on`, `ENVIRONMENT_MODE=production`)
   - Uses Africa's Talking **Production** credentials
   - Sends real SMS to actual phone numbers
   - Best for: Live deployment

---

## Quick Start (Terminal Mode)

### Step 1: Start Backend

```bash
cd backend
python start.py
```

**Expected Output:**
```
✅ Africa's Talking SMS client initialized successfully (DEVELOPMENT/SANDBOX mode)
   Username: sandbox, Sender ID: AFRICASTKNG
✅ SMTP configured - Host: smtp.gmail.com:587
📊 External API Validation Results:
==================================================
✅ Gemini: Available
✅ Google Vision: Available
✅ Climatiq: Available
✅ Africas Talking Sms: Available
⚠️ Smtp Email: Unavailable (password not configured)
==================================================
```

### Step 2: Start Frontend

```bash
cd frontend-web
npm run dev
```

### Step 3: Test OTP Flow

1. Open browser: `http://localhost:5173`
2. Import OTP component in your app
3. Enter phone number: `+254712345678`
4. Click "Send Verification Code"
5. **Check backend console** for OTP:

```
╔════════════════════════════════════════════════════════════╗
║           TERMINAL MODE - OTP DELIVERY                     ║
║                    (OTP_MODE=off)                          ║
╠════════════════════════════════════════════════════════════╣
║  Environment: DEVELOPMENT                                  ║
║  Contact Type: PHONE                                       ║
║  Recipient: +254712345678                                  ║
║                                                            ║
║  🔐 OTP CODE:              123456                          ║
║                                                            ║
║  Expires: 5 minutes                                        ║
║  Timestamp: 2025-10-01 14:30:45                            ║
║                                                            ║
║  ℹ️  Set OTP_MODE=on to enable SMS/Email delivery         ║
╚════════════════════════════════════════════════════════════╝
```

6. Enter OTP code in frontend: `123456`
7. Click "Verify & Continue"
8. ✅ Success! You're authenticated

---

## Development Mode (Africa's Talking Sandbox)

### Configuration

**File:** `backend/.env`
```bash
OTP_MODE=on
ENVIRONMENT_MODE=development
```

### Important Notes

- **Sandbox Limitations:**
  - SMS only sent to verified test numbers
  - Add test numbers in Africa's Talking dashboard
  - No actual SMS delivery cost
  - Perfect for testing integration

### Testing Steps

1. Update `.env` as shown above
2. Restart backend
3. Add test phone number in Africa's Talking sandbox dashboard
4. Send OTP via frontend
5. **Check your phone** for SMS
6. SMS Format:
```
Your HaliCred verification code is:

123456

Valid for 5 minutes. Do not share this code.

- HaliCred Team
```

---

## Production Mode (Live SMS)

### Configuration

**File:** `backend/.env`
```bash
OTP_MODE=on
ENVIRONMENT_MODE=production

# Production Credentials (ALREADY CONFIGURED)
AFRICAS_TALKING_USERNAME_PRODUCTION=HaliCred
AFRICAS_TALKING_API_KEY_PRODUCTION=atsk_0e0e55d12a9e41f686e6b566d1545f097f2249ef0e98130bd9e1437c2406330a9581ad5a
AFRICAS_TALKING_SENDER_ID_PRODUCTION=HALICRED
```

### ⚠️ Production Checklist

- [ ] Verify production API key is active
- [ ] Confirm sufficient SMS credits
- [ ] Test with your own phone number first
- [ ] Monitor costs via Africa's Talking dashboard
- [ ] Set spending limits if needed

### Cost Monitoring

- Average cost: ~KES 0.80 per SMS (Kenya)
- Monitor at: https://account.africastalking.com
- Set alerts for budget thresholds

---

## Email Configuration (Optional)

### SMTP Setup

**File:** `backend/.env`
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM_EMAIL=noreply@halicred.com
SMTP_FROM_NAME=HaliCred Support
```

### Gmail App Password Setup

1. Go to Google Account Settings
2. Security → 2-Step Verification
3. App Passwords
4. Generate password for "Mail"
5. Copy password to `SMTP_PASSWORD`

### Testing Email

```bash
curl -X POST http://localhost:8000/auth/otp \
  -H "Content-Type: application/json" \
  -d '{"email": "your-test@email.com"}'
```

Check your inbox (and spam folder) for beautifully formatted HTML email with OTP.

---

## Frontend Integration

### Option 1: Standalone Login Page

```tsx
import { OTPLogin } from './Components/Auth/OTPLogin';

function App() {
  const handleLoginSuccess = (token: string, user: any) => {
    // Store token
    localStorage.setItem('token', token);
    // Navigate to dashboard
    window.location.href = '/dashboard';
  };

  return (
    <OTPLogin
      onLoginSuccess={handleLoginSuccess}
      userType="borrower"  // or "underwriter" for bank portal
    />
  );
}
```

### Option 2: Modal/Dialog

```tsx
import { OTPLogin } from './Components/Auth/OTPLogin';
import { Dialog, DialogContent } from './Components/Ui/dialog';

function App() {
  const [showLogin, setShowLogin] = useState(false);

  return (
    <>
      <Button onClick={() => setShowLogin(true)}>Login</Button>

      <Dialog open={showLogin} onOpenChange={setShowLogin}>
        <DialogContent>
          <OTPLogin
            onLoginSuccess={(token, user) => {
              setShowLogin(false);
              // Handle authentication
            }}
          />
        </DialogContent>
      </Dialog>
    </>
  );
}
```

---

## API Endpoints

### Request OTP

**POST** `/auth/otp`

**Phone Request:**
```json
{
  "phone": "+254712345678"
}
```

**Email Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "status": "sent",
  "message": "OTP sent successfully",
  "expires_in": 300
}
```

### Verify OTP

**POST** `/auth/verify`

**Request:**
```json
{
  "phone": "+254712345678",
  "code": "123456",
  "full_name": "John Doe",
  "roles": ["borrower"]
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "uuid",
    "phone": "+254712345678",
    "email": null,
    "full_name": "John Doe",
    "roles": ["borrower"]
  },
  "last_otp_verified_at": "2025-10-01T14:30:45Z",
  "last_login_at": "2025-10-01T14:30:45Z"
}
```

---

## Health Check

### Check System Status

```bash
curl http://localhost:8000/health
```

**Response includes OTP service status:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-01T14:30:45Z",
  "services": {
    "otp_delivery": {
      "status": "healthy",
      "response_time_ms": 2.5,
      "details": {
        "otp_mode": "on",
        "environment_mode": "development",
        "africas_talking_status": "initialized",
        "africas_talking_username": "sandbox",
        "africas_talking_env": "development",
        "smtp_status": "configured"
      }
    }
  }
}
```

---

## Troubleshooting

### Issue: "Africa's Talking SMS client not initialized"

**Solution:**
- Check API key in `.env`
- Verify `ENVIRONMENT_MODE` matches credentials
- Restart backend after `.env` changes

### Issue: "OTP not received on phone"

**Development Mode:**
- Add phone number to sandbox test numbers
- Check Africa's Talking dashboard for delivery status

**Production Mode:**
- Verify phone number format includes country code
- Check SMS credits balance
- Review Africa's Talking logs for errors

### Issue: "SMTP authentication failed"

**Solution:**
- Use app-specific password for Gmail (not account password)
- Enable "Less secure app access" if using other providers
- Check SMTP_HOST and SMTP_PORT values
- Test SMTP connection with telnet

### Issue: "Rate limit exceeded"

**Solution:**
- Wait 10 minutes before next attempt
- Rate limit: 3 OTP requests per 10 minutes per identifier
- Clear Redis if testing: `redis-cli FLUSHDB`

---

## Security Features

### Built-in Protection

1. **Rate Limiting:** 3 requests per 10 minutes per phone/email
2. **OTP Expiration:** 5 minutes TTL
3. **One-Time Use:** OTP deleted after successful verification
4. **Hash Storage:** OTPs stored as SHA-256 hashes in Redis
5. **Input Validation:** Phone/email format validation
6. **Secure Transport:** HTTPS recommended for production

### Best Practices

- ✅ Always use HTTPS in production
- ✅ Monitor Africa's Talking for unusual patterns
- ✅ Set spending limits on Africa's Talking account
- ✅ Implement fraud detection for suspicious requests
- ✅ Log all OTP requests for audit trail

---

## Testing Checklist

### Terminal Mode
- [ ] Backend starts without errors
- [ ] OTP printed to console with proper formatting
- [ ] OTP verification works with printed code
- [ ] JWT token issued successfully

### Development Mode (Sandbox)
- [ ] Africa's Talking client initializes
- [ ] Test phone number receives SMS
- [ ] SMS format correct and readable
- [ ] OTP verification works with received code
- [ ] Delivery logs appear in Africa's Talking dashboard

### Production Mode
- [ ] Production credentials configured
- [ ] Real phone number receives SMS
- [ ] SMS sender ID shows "HALICRED"
- [ ] Cost per SMS acceptable
- [ ] Monitoring alerts configured

### Email Testing
- [ ] SMTP configured correctly
- [ ] Test email received in inbox (not spam)
- [ ] HTML email renders properly
- [ ] OTP code clearly visible
- [ ] Security notice included

### Frontend Testing
- [ ] Phone/Email toggle works
- [ ] Input validation prevents invalid formats
- [ ] Loading states show correctly
- [ ] Error messages display properly
- [ ] Success flow completes to dashboard
- [ ] Countdown timer works
- [ ] Resend button disabled for 60 seconds

---

## Production Deployment

### Environment Variables Checklist

**Backend `.env`:**
```bash
✅ OTP_MODE=on
✅ ENVIRONMENT_MODE=production
✅ AFRICAS_TALKING_USERNAME_PRODUCTION=HaliCred
✅ AFRICAS_TALKING_API_KEY_PRODUCTION=<your_key>
✅ AFRICAS_TALKING_SENDER_ID_PRODUCTION=HALICRED
✅ SMTP_HOST=<your_host>
✅ SMTP_USERNAME=<your_email>
✅ SMTP_PASSWORD=<app_password>
```

**Frontend `.env`:**
```bash
✅ VITE_API_BASE_URL=https://your-production-api.com
```

### Deployment Steps

1. Update production `.env` files
2. Build frontend: `npm run build`
3. Deploy backend with new environment variables
4. Test with your own phone number first
5. Monitor logs for 24 hours
6. Set up alerting for errors
7. Document incident response procedures

---

## Monitoring & Maintenance

### Daily Checks
- Review Africa's Talking SMS delivery rates
- Monitor Redis memory usage
- Check error rates in logs
- Verify health endpoint status

### Weekly Tasks
- Review SMS costs vs budget
- Analyze OTP request patterns
- Check for suspicious activity
- Update documentation if needed

### Monthly Tasks
- Rotate SMTP passwords
- Review and update rate limits
- Analyze user feedback
- Plan capacity scaling

---

## Support & Resources

### Documentation
- Africa's Talking Docs: https://developers.africastalking.com/docs
- Implementation Plan: `docs/codebase-analysis-2025-10-01/04-IMPLEMENTATION-PLAN.md`
- API Analysis: `docs/codebase-analysis-2025-10-01/03-OTP-ANALYSIS.md`

### Code Locations
- Backend Service: `backend/app/services/otp_service.py`
- Auth Endpoint: `backend/app/api/auth.py`
- Frontend Component: `frontend-web/src/Components/Auth/OTPLogin.tsx`
- Configuration: `backend/app/config.py`

### Troubleshooting
- Health Check: `GET http://localhost:8000/health`
- Logs: Check backend console output
- Redis Monitor: `redis-cli MONITOR`
- Africa's Talking Dashboard: https://account.africastalking.com

---

## Success Criteria

### ✅ Implementation Complete When:

- [x] Backend OTP service created
- [x] Africa's Talking integrated (dev & prod)
- [x] SMTP email configured
- [x] Startup validation includes OTP services
- [x] Health check includes OTP status
- [x] Frontend UI component created
- [x] Terminal mode works for testing
- [x] Development mode tested with sandbox
- [ ] Production mode tested with real phone
- [ ] Email delivery tested and working
- [ ] End-to-end flow tested successfully
- [ ] Documentation complete

---

**Status:** READY FOR TESTING
**Next Step:** Test complete OTP flow end-to-end in terminal mode
**Estimated Time:** 15 minutes for full test cycle

---

*Last Updated: October 1, 2025*
*Version: 1.0.0*
