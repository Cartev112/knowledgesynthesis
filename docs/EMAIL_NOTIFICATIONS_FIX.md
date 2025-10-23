# Email Notifications Fix

## Problem

You weren't receiving emails after ingestion completion because:

1. **Email service was never called** - The worker didn't have code to send notifications
2. **Email service disabled by default** - `EMAIL_ENABLED` environment variable defaults to `false`
3. **No email provider configured** - SendGrid or SMTP credentials not set up

## Solution Applied

### 1. ✅ Added Email Notification to Worker

**File:** `app/worker.py`

**Changes:**
- Imported `send_upload_notification` from email service
- Added email sending after successful job completion
- Extracts user email, name from job data
- Sends notification with document details and triplet count
- Gracefully handles email failures (logs warning, doesn't fail job)

**Code Added:**
```python
# Send email notification if user email is provided
user_email = job_data.get('user_email')
if user_email:
    try:
        user_first_name = job_data.get('user_first_name', '')
        user_last_name = job_data.get('user_last_name', '')
        user_name = f"{user_first_name} {user_last_name}".strip() or "User"
        
        # Run async email send in sync context
        asyncio.run(send_upload_notification(
            user_email=user_email,
            user_name=user_name,
            document_title=result['document_title'],
            document_id=result['document_id'],
            triplet_count=result['triplets_written']
        ))
        logger.info(f"Email notification sent to {user_email}")
    except Exception as email_error:
        logger.warning(f"Failed to send email notification: {email_error}")
```

---

## Configuration Required

To actually **receive emails**, you need to configure environment variables:

### Option 1: SendGrid (Recommended)

SendGrid is easier to set up and more reliable for transactional emails.

**Environment Variables:**
```bash
EMAIL_ENABLED=true
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your_sendgrid_api_key_here
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=Knowledge Synthesis
APP_URL=https://your-app-url.com
```

**Steps:**
1. Sign up at [SendGrid](https://sendgrid.com/) (free tier: 100 emails/day)
2. Create an API key in SendGrid dashboard
3. Verify your sender email address
4. Add environment variables to your `.env` file
5. Restart the worker

### Option 2: SMTP (Gmail, Outlook, etc.)

Use your existing email account's SMTP server.

**Environment Variables:**
```bash
EMAIL_ENABLED=true
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_FROM_NAME=Knowledge Synthesis
APP_URL=https://your-app-url.com
```

**For Gmail:**
1. Enable 2-factor authentication
2. Generate an "App Password" (not your regular password)
3. Use the app password in `SMTP_PASSWORD`

**For Outlook/Office 365:**
```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
```

---

## Email Template

The email sent includes:

### Subject
```
✅ Document Processed: [Document Title]
```

### Content
- **Greeting**: "Hi [User Name],"
- **Success message**: Document processed successfully
- **Document details**:
  - Title
  - Document ID
  - Number of relationships extracted
  - Upload timestamp
- **Action button**: "View in Knowledge Graph" (links to viewing tab)
- **Footer**: Branding and support info

### HTML Email Preview
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        .container { max-width: 600px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .button { background: #667eea; color: white; padding: 12px 24px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Document Processed Successfully</h1>
        </div>
        <p>Hi [User Name],</p>
        <p>Your document has been processed and added to the knowledge graph!</p>
        <div class="details">
            <strong>Document:</strong> [Title]<br>
            <strong>Relationships Extracted:</strong> [Count]<br>
            <strong>Processed:</strong> [Timestamp]
        </div>
        <a href="[View URL]" class="button">View in Knowledge Graph</a>
    </div>
</body>
</html>
```

---

## Testing

### 1. Check Email Service Status

Add this to your worker logs to see if email is enabled:

```python
from app.services.email_service import email_service
logger.info(f"Email service enabled: {email_service.enabled}")
logger.info(f"Email provider: {email_service.provider}")
```

### 2. Test Email Sending

Create a test script:

```python
import asyncio
from app.services.email_service import send_upload_notification

async def test_email():
    result = await send_upload_notification(
        user_email="your-email@example.com",
        user_name="Test User",
        document_title="Test Document.pdf",
        document_id="test-123",
        triplet_count=42
    )
    print(f"Email sent: {result}")

asyncio.run(test_email())
```

### 3. Check Worker Logs

After ingestion, look for:
```
Email notification sent to user@example.com
```

Or if it failed:
```
Failed to send email notification: [error message]
```

---

## Troubleshooting

### Issue: "Email service disabled"

**Cause:** `EMAIL_ENABLED` not set to `true`

**Fix:**
```bash
EMAIL_ENABLED=true
```

### Issue: "SendGrid error: 401"

**Cause:** Invalid API key

**Fix:**
1. Check API key is correct
2. Verify API key has "Mail Send" permission
3. Regenerate API key if needed

### Issue: "SMTP authentication failed"

**Cause:** Wrong credentials or 2FA not configured

**Fix for Gmail:**
1. Enable 2-factor authentication
2. Generate App Password at https://myaccount.google.com/apppasswords
3. Use App Password, not regular password

### Issue: "Email sent but not received"

**Possible causes:**
1. **Spam folder** - Check spam/junk
2. **Sender not verified** - Verify sender email in SendGrid
3. **Rate limit** - Free tier limits (100/day for SendGrid)
4. **Firewall** - Check if SMTP port 587 is blocked

### Issue: "No user email in job data"

**Cause:** Frontend not sending user email

**Fix:** Ensure ingestion API includes `user_email` in job data

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EMAIL_ENABLED` | Yes | `false` | Enable/disable email notifications |
| `EMAIL_PROVIDER` | Yes | `sendgrid` | `sendgrid` or `smtp` |
| `SENDGRID_API_KEY` | If SendGrid | - | SendGrid API key |
| `SMTP_HOST` | If SMTP | `smtp.gmail.com` | SMTP server hostname |
| `SMTP_PORT` | If SMTP | `587` | SMTP server port |
| `SMTP_USER` | If SMTP | - | SMTP username/email |
| `SMTP_PASSWORD` | If SMTP | - | SMTP password/app password |
| `EMAIL_FROM` | No | `noreply@knowledgesynthesis.app` | Sender email address |
| `EMAIL_FROM_NAME` | No | `Knowledge Synthesis` | Sender display name |
| `APP_URL` | No | `http://localhost:8000` | Base URL for links in email |

---

## Production Recommendations

### 1. Use SendGrid

- More reliable than SMTP
- Better deliverability
- Email analytics
- Bounce/spam handling
- Free tier sufficient for most use cases

### 2. Verify Sender Domain

- Set up SPF, DKIM, DMARC records
- Verify domain in SendGrid
- Use branded domain (not @gmail.com)

### 3. Monitor Email Delivery

- Check SendGrid dashboard for delivery stats
- Monitor bounce rates
- Track open rates (optional)

### 4. Handle Failures Gracefully

- Current implementation: logs warning, doesn't fail job ✅
- Consider: retry logic for transient failures
- Consider: dead letter queue for persistent failures

### 5. Rate Limiting

- SendGrid free: 100 emails/day
- SendGrid paid: 40,000+ emails/month
- Implement queuing if high volume

---

## Next Steps

1. **Choose email provider** (SendGrid recommended)
2. **Set up account** and get credentials
3. **Add environment variables** to `.env` file
4. **Restart worker** to load new config
5. **Test** by uploading a document
6. **Check email** (and spam folder!)
7. **Monitor logs** for email sending status

---

## Security Notes

- ⚠️ Never commit API keys or passwords to git
- ✅ Use environment variables for all credentials
- ✅ Use app passwords for Gmail (not regular password)
- ✅ Restrict SendGrid API key to "Mail Send" only
- ✅ Rotate credentials regularly
- ✅ Use HTTPS for all email links

---

## Files Modified

1. **`app/worker.py`**
   - Added email notification after job completion
   - Imported email service and asyncio
   - Graceful error handling

2. **`app/services/email_service.py`** (already existed)
   - Email service implementation
   - SendGrid and SMTP support
   - HTML email templates

---

## Status

- ✅ Email notification code added to worker
- ⚠️ **Configuration required** - Set environment variables
- ⚠️ **Testing required** - Verify emails are received

**To receive emails, you must:**
1. Set `EMAIL_ENABLED=true`
2. Configure SendGrid or SMTP credentials
3. Restart the worker
