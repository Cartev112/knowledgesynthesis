# Email Notification Setup Guide

Your application now sends beautiful email confirmations to users when their documents are successfully processed! 

This feature is **optional** and gracefully degrades if not configured.

---

## 🎯 What Users Receive

When a document is uploaded and processed, users automatically receive:

✅ **Professional HTML email** with:
- Document title and processing details
- Number of relationships extracted
- Direct link to view in the graph viewer
- Next steps and recommendations

📱 **Mobile-responsive** and works in all email clients

---

## 🚀 Quick Setup (3 Options)

### Option 1: SendGrid (Recommended) ⭐

**Why SendGrid?**
- ✅ **100 emails/day free** forever
- ✅ Easy setup (5 minutes)
- ✅ Professional email delivery
- ✅ Great deliverability

**Setup Steps:**

1. **Create SendGrid Account**
   - Go to [sendgrid.com](https://sendgrid.com)
   - Sign up for free account
   - Verify your email

2. **Create API Key**
   - Dashboard → Settings → API Keys
   - Click "Create API Key"
   - Name: `Knowledge Synthesis`
   - Permissions: **Full Access** (or just "Mail Send")
   - Copy the API key (you won't see it again!)

3. **Configure Your App**
   
   Add to your `.env` file:
   ```bash
   EMAIL_ENABLED=true
   EMAIL_PROVIDER=sendgrid
   SENDGRID_API_KEY=SG.your-key-here
   EMAIL_FROM=noreply@knowledgesynthesis.app
   EMAIL_FROM_NAME=Knowledge Synthesis
   APP_URL=http://localhost:8000  # or your production URL
   ```

4. **Verify Sender** (Important!)
   - SendGrid → Settings → Sender Authentication
   - Choose "Single Sender Verification"
   - Add your email (e.g., `noreply@gmail.com`)
   - Verify via email link
   - Update `EMAIL_FROM` to match verified email

5. **Test It!**
   - Restart your backend
   - Upload a document
   - Check your email! 📧

**Free Tier Limits:**
- 100 emails/day (3,000/month)
- Perfect for development and small deployments

---

### Option 2: Gmail SMTP (Simple)

**Good for:** Testing, personal use

**Setup Steps:**

1. **Enable App Passwords**
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Turn on 2-Step Verification (required)
   - Search for "App passwords"
   - Generate app password for "Mail"
   - Copy the 16-character password

2. **Configure Your App**
   
   Add to your `.env` file:
   ```bash
   EMAIL_ENABLED=true
   EMAIL_PROVIDER=smtp
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   EMAIL_FROM=your-email@gmail.com
   EMAIL_FROM_NAME=Knowledge Synthesis
   APP_URL=http://localhost:8000
   ```

3. **Test It!**
   - Restart your backend
   - Upload a document
   - Check recipient email

**Limitations:**
- 500 emails/day limit
- May end up in spam folder
- Not ideal for production

---

### Option 3: Custom SMTP Server

**Good for:** Organizations with existing email infrastructure

**Setup:**

```bash
EMAIL_ENABLED=true
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.yourcompany.com
SMTP_PORT=587
SMTP_USER=your-smtp-username
SMTP_PASSWORD=your-smtp-password
EMAIL_FROM=noreply@yourcompany.com
EMAIL_FROM_NAME=Knowledge Synthesis
APP_URL=https://yourdomain.com
```

---

## 🔒 Security Best Practices

1. **Never commit `.env` file** to git (already in `.gitignore`)
2. **Use environment variables** in production
3. **Rotate API keys** periodically
4. **Use app-specific passwords** for SMTP
5. **Enable 2FA** on email provider accounts

---

## 🧪 Testing Email Setup

### Test Locally

1. Start your backend:
   ```bash
   cd backend/python_worker
   uvicorn app.main:app --reload
   ```

2. Upload a test document via the UI

3. Check logs for:
   ```
   INFO:app.routes.ingest:Scheduled email notification for user@example.com
   INFO:app.services.email_service:Email sent successfully to user@example.com
   ```

### Test API Directly

```bash
# Using curl
curl -X POST http://localhost:8000/ingest/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Test content",
    "document_title": "Test Doc",
    "user_email": "your-email@example.com",
    "user_first_name": "John",
    "user_last_name": "Doe"
  }'
```

---

## 🎨 Email Preview

The emails look like this:

```
┌─────────────────────────────────────┐
│    ✅ Document Processed            │  ← Purple gradient header
├─────────────────────────────────────┤
│                                     │
│  Hi John Doe,                       │
│                                     │
│  Your document has been             │
│  successfully processed!            │
│                                     │
│  ┌─────────────────────────────┐  │
│  │ 📄 Research Paper.pdf       │  │
│  │ • Relationships: 42          │  │
│  │ • Processed: Oct 2, 2025    │  │
│  │ • Document ID: abc123...     │  │
│  └─────────────────────────────┘  │
│                                     │
│      [View in Graph Viewer →]      │
│                                     │
│  💡 Next Steps:                     │
│  • Review relationships             │
│  • Verify accuracy                  │
│  • Upload more documents            │
│                                     │
└─────────────────────────────────────┘
```

---

## 🚫 Disable Emails

To turn off email notifications:

```bash
EMAIL_ENABLED=false
```

Or simply don't set the environment variable. The app works perfectly without emails!

---

## 🐛 Troubleshooting

### "Email service disabled" in logs
- Check `EMAIL_ENABLED=true` in `.env`
- Restart the backend after changing `.env`

### "SENDGRID_API_KEY not configured"
- Verify API key is in `.env`
- Check for typos in key
- Ensure no extra spaces/quotes

### Emails going to spam
- **SendGrid**: Complete sender authentication
- **Gmail**: Use app passwords, not regular password
- **Custom domain**: Set up SPF, DKIM records

### "SendGrid error: 403"
- Verify sender email in SendGrid dashboard
- Check API key has "Mail Send" permission

### No email received
- Check spam folder
- Verify recipient email is correct
- Check backend logs for errors
- Test with different email address

### "Failed to send upload confirmation email"
- Check network connectivity
- Verify SMTP port (587 for TLS, 465 for SSL)
- Try different SMTP provider

---

## 📊 Production Deployment

### Environment Variables for Render/Railway

Add these to your deployment platform:

```bash
EMAIL_ENABLED=true
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=Knowledge Synthesis
APP_URL=https://your-app.onrender.com
```

### Custom Domain Email (Professional)

1. **Purchase domain** (e.g., via Namecheap, Google Domains)
2. **Set up email forwarding** or Google Workspace
3. **Configure SendGrid** with domain authentication
4. **Update `EMAIL_FROM`** to `noreply@yourdomain.com`
5. **Add DNS records** (SPF, DKIM, DMARC)

---

## 💰 Cost Comparison

| Provider | Free Tier | Paid Plans |
|----------|-----------|------------|
| **SendGrid** | 100/day (3k/month) | $15/mo for 40k emails |
| **Gmail SMTP** | 500/day | Not for commercial use |
| **Mailgun** | 1,000/month | $35/mo for 50k emails |
| **AWS SES** | 3,000/month (if on EC2) | $0.10 per 1,000 emails |

**Recommendation:** Start with SendGrid free tier

---

## 🎓 Advanced Customization

### Custom Email Template

Edit `backend/python_worker/app/services/email_service.py`:

```python
def _build_upload_email_html(self, ...):
    return f"""
    <!-- Your custom HTML template -->
    """
```

### Add More Email Types

```python
async def send_verification_complete(self, user_email, relationship_id):
    """Send notification when expert verifies a relationship."""
    # Implement similar to send_upload_confirmation
```

### Schedule Digest Emails

Use a task scheduler (Celery, APScheduler) to send weekly summaries.

---

## ✅ Quick Checklist

Before going live:

- [ ] Email provider configured (SendGrid recommended)
- [ ] Sender email verified
- [ ] Test email sent and received
- [ ] Not landing in spam
- [ ] `APP_URL` set to production URL
- [ ] API keys secured (not in git)
- [ ] Logging working (check for email errors)
- [ ] Backup email provider configured (optional)

---

## 📞 Support

Having issues? Check:
1. Backend logs for error messages
2. Email provider dashboard for bounces
3. Network connectivity (firewall blocking SMTP?)
4. Try different email provider for comparison

**Common Solutions:**
- 90% of issues: API key typos or not restarting server
- 5%: Sender verification not completed
- 5%: Firewall blocking SMTP ports

---

## 🎉 You're All Set!

Your users will now receive beautiful confirmation emails when their documents are processed. This professional touch makes your application feel polished and production-ready!

**Next Steps:**
- Test with real documents
- Monitor email delivery rates
- Consider upgrading to paid plan if needed
- Set up monitoring/alerts for failed emails

Happy emailing! 📧✨








