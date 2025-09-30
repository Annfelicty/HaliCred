# HaliCred Troubleshooting Guide

## Overview

This guide provides comprehensive troubleshooting information for common issues encountered on the HaliCred platform. It covers both SME users and bank portal users, with step-by-step solutions and escalation procedures.

## Quick Diagnostic Tools

### Health Check Commands

#### Application Status
```bash
# Check overall system health
curl https://api.halicred.com/health

# Check specific services
curl https://api.halicred.com/health/db
curl https://api.halicred.com/health/ai
curl https://api.halicred.com/health/redis
```

#### Browser-Based Diagnostics
1. **Open Developer Console**: F12 (Chrome/Firefox) or Cmd+Option+I (Safari)
2. **Check Console Errors**: Look for red error messages
3. **Network Tab**: Check for failed API requests
4. **Application Tab**: Verify local storage and cookies

### Common Error Codes

| Error Code | Description | Common Cause |
|------------|-------------|--------------|
| API_001 | Authentication failed | Invalid or expired token |
| API_002 | Rate limit exceeded | Too many requests |
| API_003 | Invalid request format | Malformed data |
| AI_001 | Gemini API unavailable | External service down |
| AI_002 | Vision processing failed | Invalid image format |
| AI_003 | Climatiq API error | Emission calculation failed |
| DB_001 | Database connection failed | Database unavailable |
| FILE_001 | Upload failed | File too large or invalid format |

## Authentication Issues

### Cannot Log In

#### Problem: OTP Not Received
**Symptoms**:
- SMS with OTP code doesn't arrive
- "Waiting for OTP" screen persists

**Solutions**:
1. **Check Phone Number Format**
   - Ensure international format: +254XXXXXXXXX
   - Remove any spaces or special characters
   - Verify country code is correct

2. **Network Issues**
   - Check mobile network signal strength
   - Try switching between WiFi and mobile data
   - Contact mobile operator if SMS issues persist

3. **SMS Delivery Delays**
   - Wait up to 5 minutes for SMS delivery
   - Check spam/junk SMS folder
   - Restart phone if SMS service seems blocked

4. **Alternative Solutions**
   - Use different phone number if available
   - Contact support for manual verification
   - Try using web app instead of mobile app

#### Problem: Invalid OTP Error
**Symptoms**:
- "Invalid OTP" message appears
- OTP seems correct but won't validate

**Solutions**:
1. **Timing Issues**
   - Ensure OTP is entered within 5 minutes
   - Request new OTP if expired
   - Check phone clock is synchronized

2. **Input Errors**
   - Double-check each digit carefully
   - Avoid copy-pasting OTP codes
   - Use manual keyboard entry

3. **Multiple Attempts**
   - Clear form and re-enter OTP
   - Request fresh OTP after 3 failed attempts
   - Wait 1 minute between retry attempts

### Session Management Issues

#### Problem: Frequent Logouts
**Symptoms**:
- Session expires quickly
- Need to re-authenticate often

**Solutions**:
1. **Browser Settings**
   - Enable cookies for halicred.com
   - Disable private/incognito browsing
   - Clear cookies and cache, then log in again

2. **App Settings**
   - Enable "Remember Me" option
   - Check app permissions for data storage
   - Update app to latest version

3. **Network Issues**
   - Use stable internet connection
   - Avoid switching between networks during session
   - Consider using mobile data instead of WiFi

#### Problem: Cannot Access Protected Pages
**Symptoms**:
- Redirected to login page repeatedly
- "Unauthorized" errors on protected routes

**Solutions**:
1. **Token Issues**
   - Log out completely and log back in
   - Clear browser storage/app data
   - Check if account has appropriate permissions

2. **Browser Problems**
   - Try different browser or device
   - Disable browser extensions temporarily
   - Update browser to latest version

## Evidence Upload Issues

### File Upload Problems

#### Problem: File Upload Fails
**Symptoms**:
- Upload progress bar stops or fails
- "Upload failed" error message
- File doesn't appear in evidence list

**Solutions**:
1. **File Size and Format**
   - Check file size is under 20MB
   - Use supported formats: JPG, PNG, PDF
   - Compress large images if necessary

2. **Network Issues**
   - Check internet connection stability
   - Try uploading during off-peak hours
   - Use WiFi instead of mobile data for large files

3. **Browser/App Issues**
   - Clear browser cache or app cache
   - Try different browser or device
   - Disable ad blockers temporarily

#### Problem: Poor Image Quality Warning
**Symptoms**:
- AI warns about image quality
- Low confidence scores on processing

**Solutions**:
1. **Improve Photo Quality**
   - Use better lighting (natural light preferred)
   - Hold camera steady to avoid blur
   - Ensure document is flat against contrasting background
   - Take photo directly above document (avoid angles)

2. **Document Preparation**
   - Smooth out wrinkles or folds
   - Clean any dirt or stains from document
   - Use scanner instead of camera if available
   - Take multiple photos from different angles

3. **Technical Settings**
   - Use highest camera resolution
   - Ensure flash is off for documents
   - Focus manually if auto-focus fails
   - Avoid shadows or reflections

### AI Processing Issues

#### Problem: Evidence Processing Takes Too Long
**Symptoms**:
- Processing status stuck on "Processing"
- No results after 5+ minutes

**Solutions**:
1. **Wait and Monitor**
   - AI processing can take 30-60 seconds normally
   - Complex documents may take up to 2 minutes
   - Check processing status every 30 seconds

2. **Technical Issues**
   - Refresh page/app after 3 minutes
   - Check internet connection stability
   - Try re-submitting if stuck over 5 minutes

3. **File Issues**
   - Ensure file isn't corrupted
   - Try uploading a different file first
   - Check if file format is definitely supported

#### Problem: Low Confidence AI Results
**Symptoms**:
- Confidence score below 60%
- AI can't identify equipment or amounts
- "Requires manual review" status

**Solutions**:
1. **Improve Evidence Quality**
   - Retake photo with better quality
   - Ensure all text is clearly readable
   - Include model numbers and specifications
   - Add detailed description of the evidence

2. **Additional Evidence**
   - Upload multiple photos of same item
   - Include installation photos showing context
   - Add before/after comparison photos
   - Upload supporting documentation

3. **Documentation Enhancement**
   - Write detailed description of sustainability impact
   - Include purchase date and location
   - Specify equipment capacity or efficiency rating
   - Mention energy or cost savings achieved

## Green Score Issues

### Score Calculation Problems

#### Problem: Green Score Not Updating
**Symptoms**:
- Score remains the same after uploading evidence
- Recent evidence not reflected in score

**Solutions**:
1. **Processing Time**
   - Wait 24 hours for score recalculation
   - Check that evidence was successfully processed
   - Verify evidence has "Verified" status

2. **Evidence Quality**
   - Ensure evidence meets minimum quality standards
   - Check confidence scores are above 60%
   - Review if evidence type matches sustainability claim

3. **Technical Issues**
   - Log out and log back in to refresh data
   - Clear browser cache or app data
   - Contact support if no update after 48 hours

#### Problem: Lower Score Than Expected
**Symptoms**:
- Score doesn't increase as much as anticipated
- High-value evidence has minimal impact

**Solutions**:
1. **Review Score Breakdown**
   - Check individual pillar scores
   - Identify which areas need improvement
   - Focus on pillars with lowest scores

2. **Evidence Impact Analysis**
   - Review each evidence item's contribution
   - Check if similar evidence was already submitted
   - Ensure evidence shows measurable impact

3. **Scoring Algorithm Understanding**
   - Learn about diminishing returns for similar evidence
   - Understand sector baselines and benchmarks
   - Balance across all four sustainability pillars

### Score Discrepancies

#### Problem: Score Seems Inaccurate
**Symptoms**:
- Score doesn't match evidence quality
- Similar businesses have very different scores

**Solutions**:
1. **Sector Comparison**
   - Compare against sector-specific baselines
   - Understand that different sectors have different scales
   - Check if business type is correctly set

2. **Evidence Verification**
   - Review all evidence for accuracy
   - Check for any rejected or low-confidence items
   - Ensure evidence represents real sustainability improvements

3. **Algorithm Updates**
   - Scores may change due to algorithm improvements
   - New evidence types may affect historical scores
   - Contact support for detailed score explanation

## Loan Application Issues

### Application Submission Problems

#### Problem: Cannot Submit Loan Application
**Symptoms**:
- Submit button doesn't work
- Error message on form submission
- Application saves as draft but won't submit

**Solutions**:
1. **Form Completion**
   - Ensure all required fields are filled
   - Check business profile is complete
   - Verify Green Score meets minimum threshold

2. **Technical Issues**
   - Try submitting from different browser/device
   - Clear form and re-enter information
   - Check internet connection during submission

3. **Account Issues**
   - Verify account is fully verified
   - Check if any additional documentation is required
   - Ensure terms and conditions are accepted

#### Problem: Loan Amount Restrictions
**Symptoms**:
- Cannot request desired loan amount
- "Amount exceeds eligibility" error
- Lower amount suggested than expected

**Solutions**:
1. **Eligibility Requirements**
   - Review eligibility criteria for your sector
   - Check if Green Score meets requirements
   - Consider improving score before reapplying

2. **Business Profile**
   - Update business size and revenue information
   - Provide more detailed business information
   - Upload additional financial documentation

3. **Alternative Approaches**
   - Start with smaller loan amount
   - Consider phased borrowing approach
   - Improve Green Score then reapply for larger amount

### Application Status Issues

#### Problem: Application Status Not Updating
**Symptoms**:
- Status stuck on "Submitted" for many days
- No communication from bank
- Cannot track application progress

**Solutions**:
1. **Normal Processing Time**
   - Allow 5-7 business days for initial review
   - Complex applications may take longer
   - Holiday periods may cause delays

2. **Follow Up Actions**
   - Check if additional documentation was requested
   - Verify contact information is current
   - Contact bank directly if over 10 business days

3. **Technical Issues**
   - Refresh application status page
   - Log out and log back in
   - Check spam folder for email updates

## Technical Platform Issues

### Performance Issues

#### Problem: Platform Running Slowly
**Symptoms**:
- Pages load slowly
- Long delays for form submissions
- Timeouts when uploading files

**Solutions**:
1. **Connection Issues**
   - Test internet speed (minimum 1 Mbps recommended)
   - Try different internet connection
   - Use WiFi instead of mobile data for large operations

2. **Browser Optimization**
   - Close unnecessary browser tabs
   - Clear browser cache and cookies
   - Disable browser extensions temporarily
   - Update browser to latest version

3. **Device Performance**
   - Close other applications
   - Restart device if performance is poor
   - Ensure device has sufficient storage space

#### Problem: Features Not Working
**Symptoms**:
- Buttons don't respond
- Forms don't submit
- Navigation issues

**Solutions**:
1. **Browser Compatibility**
   - Use supported browsers (Chrome, Firefox, Safari, Edge)
   - Update browser to latest version
   - Try different browser to isolate issue

2. **JavaScript Issues**
   - Enable JavaScript in browser settings
   - Disable ad blockers temporarily
   - Check browser console for error messages

3. **Platform Maintenance**
   - Check if planned maintenance is occurring
   - Try accessing during different hours
   - Contact support to verify system status

### Mobile App Issues

#### Problem: Mobile App Crashes
**Symptoms**:
- App closes unexpectedly
- Cannot open specific features
- App freezes during use

**Solutions**:
1. **App Updates**
   - Update to latest app version
   - Check app store for pending updates
   - Install critical security updates

2. **Device Issues**
   - Restart mobile device
   - Clear app cache and data
   - Ensure sufficient storage space

3. **Reinstallation**
   - Uninstall and reinstall app
   - Back up any important data first
   - Re-login and verify all features work

#### Problem: Push Notifications Not Working
**Symptoms**:
- Not receiving application status updates
- Missing important notifications
- Notification settings seem correct

**Solutions**:
1. **Permission Settings**
   - Check app has notification permissions
   - Enable notifications in device settings
   - Allow background app refresh

2. **Platform Settings**
   - Verify notification preferences in app
   - Check if Do Not Disturb is enabled
   - Test notifications with a small action

3. **Technical Issues**
   - Force close and restart app
   - Log out and log back in
   - Update app to latest version

## Bank Portal Issues

### Access and Authentication

#### Problem: Bank Portal Login Issues
**Symptoms**:
- Cannot access bank.halicred.com
- Multi-factor authentication problems
- "Unauthorized access" errors

**Solutions**:
1. **Credential Verification**
   - Verify username and password
   - Check if account is still active
   - Contact bank administrator for reset

2. **MFA Issues**
   - Sync authenticator app time
   - Use backup codes if available
   - Contact IT support for MFA reset

3. **Network Issues**
   - Check if bank firewall blocks access
   - Try from different network
   - Verify VPN settings if required

### Data and Analytics Issues

#### Problem: Portfolio Data Not Loading
**Symptoms**:
- Empty dashboards
- "No data available" messages
- Old data showing

**Solutions**:
1. **Permission Issues**
   - Verify user role has appropriate access
   - Check data filtering settings
   - Contact administrator for permission review

2. **Date Range Settings**
   - Adjust date filters to include data
   - Check if data exists for selected period
   - Reset filters to default settings

3. **Technical Issues**
   - Refresh browser page
   - Clear browser cache
   - Try different browser or device

## Error Code Reference

### API Error Codes

#### Authentication Errors (AUTH_XXX)
- **AUTH_001**: Invalid credentials
- **AUTH_002**: Token expired
- **AUTH_003**: Insufficient permissions
- **AUTH_004**: Account locked
- **AUTH_005**: MFA required

#### Validation Errors (VAL_XXX)
- **VAL_001**: Missing required field
- **VAL_002**: Invalid data format
- **VAL_003**: File too large
- **VAL_004**: Unsupported file type
- **VAL_005**: Invalid phone number format

#### Processing Errors (PROC_XXX)
- **PROC_001**: AI processing failed
- **PROC_002**: OCR extraction failed
- **PROC_003**: Image analysis failed
- **PROC_004**: Emission calculation failed
- **PROC_005**: Score calculation failed

#### System Errors (SYS_XXX)
- **SYS_001**: Database connection failed
- **SYS_002**: External service unavailable
- **SYS_003**: Rate limit exceeded
- **SYS_004**: Server overloaded
- **SYS_005**: Maintenance mode

### Resolution Steps by Error Code

#### AUTH_002: Token Expired
1. Log out completely
2. Clear browser cookies/app data
3. Log back in with credentials
4. Ensure "Remember Me" is selected

#### VAL_003: File Too Large
1. Check file size (max 20MB)
2. Compress image if necessary
3. Use image optimization tools
4. Try uploading via web instead of mobile

#### PROC_001: AI Processing Failed
1. Wait 5 minutes and try again
2. Check if all AI services are operational
3. Try uploading different evidence first
4. Contact support if issue persists

#### SYS_003: Rate Limit Exceeded
1. Wait for rate limit reset (usually 1 hour)
2. Reduce frequency of requests
3. Use efficient batch operations
4. Contact support for rate limit increase

## Escalation Procedures

### When to Contact Support

#### Immediate Escalation (Critical Issues)
- Cannot log in after trying all solutions
- Data loss or corruption
- Payment processing failures
- Security-related concerns

#### Standard Escalation (Non-Critical Issues)
- Feature not working after troubleshooting
- Score discrepancies requiring explanation
- Performance issues persisting over 24 hours
- Integration problems

### Support Contact Methods

#### Self-Service Options
1. **Knowledge Base**: docs.halicred.com
2. **FAQ Section**: app.halicred.com/help
3. **Video Tutorials**: YouTube channel
4. **Community Forum**: community.halicred.com

#### Direct Support
1. **Email Support**: support@halicred.com
2. **Live Chat**: Available 8 AM - 6 PM EAT
3. **Phone Support**: +254-XXX-XXXXXX
4. **WhatsApp**: +254-XXX-XXXXXX

#### Enterprise Support (Banks)
1. **Dedicated Account Manager**: For institutional accounts
2. **Technical Support**: bank-support@halicred.com
3. **Emergency Hotline**: 24/7 for critical issues
4. **Video Conferencing**: For complex technical issues

### Information to Provide When Contacting Support

#### Basic Information
- Account email/phone number
- User type (SME or Bank)
- Browser/app version
- Operating system
- Time when issue occurred

#### Error Details
- Exact error message
- Error code (if available)
- Steps taken before error
- Screenshots of error
- Network connection type

#### For Evidence Issues
- File type and size
- Equipment/evidence type
- Photo quality assessment
- Previous successful uploads

#### For Score Issues
- Current Green Score
- Expected score change
- Evidence items involved
- Business sector
- Timeline of changes

## Preventive Measures

### Best Practices for Users

#### Account Security
1. Use strong, unique passwords
2. Enable two-factor authentication
3. Log out when using shared devices
4. Regular password updates

#### Evidence Management
1. Take high-quality photos
2. Organize evidence by type
3. Upload evidence promptly
4. Keep backup copies of important documents

#### Performance Optimization
1. Use updated browsers/apps
2. Maintain good internet connection
3. Regular cache clearing
4. Monitor device storage

### System Maintenance

#### Regular Maintenance Windows
- **Weekly**: Sunday 2-4 AM EAT
- **Monthly**: First Saturday 12-6 AM EAT
- **Quarterly**: Major updates with advance notice

#### Scheduled Maintenance Notifications
- Email notifications 48 hours in advance
- In-app notifications 24 hours prior
- Status page updates during maintenance
- Post-maintenance verification reports

---

**Document Version**: 7.0.0
**Last Updated**: September 30, 2025
**Support Team**: HaliCred Technical Support
**Emergency Contact**: emergency@halicred.com