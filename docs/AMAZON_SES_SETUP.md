# Amazon SES Email Setup Guide

This guide will help you configure Amazon SES (Simple Email Service) for Adapterly.

## Prerequisites

- AWS Account
- Access to AWS SES Console
- A verified email address or domain

## Step 1: Verify Your Email Address or Domain

### Option A: Verify a Single Email Address

1. Go to [AWS SES Console](https://console.aws.amazon.com/ses/)
2. Click **Verified identities** in the left menu
3. Click **Create identity**
4. Select **Email address**
5. Enter your email address (e.g., `noreply@yourdomain.com`)
6. Click **Create identity**
7. Check your email and click the verification link
8. Wait for status to change to **Verified**

### Option B: Verify Your Domain (Recommended for Production)

1. Go to [AWS SES Console](https://console.aws.amazon.com/ses/)
2. Click **Verified identities** in the left menu
3. Click **Create identity**
4. Select **Domain**
5. Enter your domain (e.g., `example.com`)
6. Enable DKIM signing (recommended)
7. Click **Create identity**
8. Add the provided DNS records to your domain:
   - DKIM records (3 CNAME records)
   - MX record (if receiving emails)
   - SPF record (TXT record)
9. Wait for DNS propagation (can take up to 72 hours)
10. Status will change to **Verified** when complete

## Step 2: Create SMTP Credentials

1. In AWS SES Console, click **SMTP settings** in the left menu
2. Note your **SMTP endpoint** (e.g., `email-smtp.eu-west-1.amazonaws.com`)
3. Click **Create SMTP credentials**
4. Enter an IAM user name (e.g., `ses-smtp-user`)
5. Click **Create**
6. **IMPORTANT:** Download or copy the credentials:
   - SMTP Username (e.g., `AKIAIOSFODNN7EXAMPLE`)
   - SMTP Password (this is shown only once!)

## Step 3: Configure Your `.env` File

Add these settings to your `.env` file:

```env
# Amazon SES Configuration
EMAIL_HOST=email-smtp.eu-west-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false

# SMTP Credentials from Step 2
EMAIL_HOST_USER=AKIAIOSFODNN7EXAMPLE
EMAIL_HOST_PASSWORD=your-smtp-password-from-step-2

# IMPORTANT: Must be a verified email or domain
DEFAULT_FROM_EMAIL=noreply@example.com
```

**Important Notes:**
- Replace `eu-west-1` with your AWS region
- `DEFAULT_FROM_EMAIL` MUST be verified in SES (Step 1)
- `EMAIL_HOST_USER` is the SMTP Username (starts with AKIA...)
- `EMAIL_HOST_PASSWORD` is the SMTP Password (NOT your AWS secret key)

## Step 4: Move Out of SES Sandbox (Production)

By default, SES is in "sandbox mode" which restricts:
- You can only send TO verified email addresses
- Maximum 200 emails per day
- 1 email per second

To remove these limits:

1. Go to [AWS SES Console](https://console.aws.amazon.com/ses/)
2. Click **Account dashboard** in the left menu
3. Click **Request production access**
4. Fill out the form:
   - **Mail type**: Transactional
   - **Website URL**: `https://example.com`
   - **Use case description**: Explain your use case (password resets, user notifications, etc.)
   - **Compliance**: How you handle bounces and complaints
5. Submit the request
6. Wait for AWS approval (usually 24-48 hours)

## Step 5: Test Your Configuration

After updating your `.env` file:

```bash
# Restart Django server
python manage.py runserver

# Send test email
python manage.py test_email admin@example.com
```

If in **sandbox mode**, the recipient email must be verified in SES first!

## Troubleshooting

### Error: "Invalid MAIL FROM address provided"

**Cause:** The `DEFAULT_FROM_EMAIL` is not verified in SES

**Solution:**
1. Verify the email address in AWS SES (Step 1)
2. Make sure `.env` has `DEFAULT_FROM_EMAIL=verified-email@domain.com`
3. Restart Django server

### Error: "Address not verified"

**Cause:** In sandbox mode, recipient email is not verified

**Solution:**
- Verify recipient email in SES, OR
- Request production access (Step 4)

### Error: "Daily sending quota exceeded"

**Cause:** Hit the sandbox limit of 200 emails/day

**Solution:**
- Request production access (Step 4)

### Error: "Configuration set does not exist"

**Cause:** Configuration set reference issue

**Solution:**
- Remove any `ConfigurationSet` references
- Use basic SMTP settings

## SES Regions

Choose the region closest to your users:

| Region | SMTP Endpoint |
|--------|--------------|
| US East (N. Virginia) | `email-smtp.us-east-1.amazonaws.com` |
| US West (Oregon) | `email-smtp.us-west-2.amazonaws.com` |
| EU (Ireland) | `email-smtp.eu-west-1.amazonaws.com` |
| EU (Frankfurt) | `email-smtp.eu-central-1.amazonaws.com` |
| Asia Pacific (Tokyo) | `email-smtp.ap-northeast-1.amazonaws.com` |
| Asia Pacific (Sydney) | `email-smtp.ap-southeast-2.amazonaws.com` |

## Monitoring

### View Email Sending Statistics

1. Go to AWS SES Console
2. Click **Account dashboard**
3. View metrics:
   - Sends
   - Deliveries
   - Bounces
   - Complaints

### Set Up SNS Notifications

To track bounces and complaints:

1. Create an SNS topic
2. Subscribe to the topic (email or webhook)
3. Configure SES notifications:
   - Go to **Verified identities**
   - Select your domain/email
   - Click **Notifications** tab
   - Configure bounce, complaint, and delivery notifications

## Cost

Amazon SES pricing (as of 2024):

- **First 62,000 emails/month**: $0 (free tier)
- **After that**: $0.10 per 1,000 emails
- **Data transfer**: $0.12 per GB

Example: 100,000 emails/month = $3.80

## Security Best Practices

1. **Use IAM policies** to limit SES access
2. **Rotate SMTP credentials** regularly
3. **Monitor bounce rates** (keep below 5%)
4. **Monitor complaint rates** (keep below 0.1%)
5. **Use DKIM signing** for better deliverability
6. **Configure SPF and DMARC** records
7. **Never commit credentials** to Git

## DNS Records for Better Deliverability

Add these DNS records to your domain:

### SPF Record (TXT)
```
v=spf1 include:amazonses.com ~all
```

### DMARC Record (TXT)
```
_dmarc.yourdomain.com
v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com
```

### DKIM Records
Use the CNAME records provided by SES during domain verification.

## Example `.env` Configuration

```env
# Amazon SES - EU West 1 (Ireland)
EMAIL_HOST=email-smtp.eu-west-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
EMAIL_HOST_USER=AKIAIOSFODNN7EXAMPLE
EMAIL_HOST_PASSWORD=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
DEFAULT_FROM_EMAIL=noreply@example.com
```

## Quick Checklist

- [ ] Email or domain verified in SES
- [ ] SMTP credentials created and saved
- [ ] `.env` file updated with credentials
- [ ] `DEFAULT_FROM_EMAIL` matches verified email/domain
- [ ] Test email sent successfully
- [ ] Production access requested (if needed)
- [ ] DNS records configured (for domain verification)
- [ ] Bounce/complaint monitoring set up

## Support

- [AWS SES Documentation](https://docs.aws.amazon.com/ses/)
- [AWS SES SMTP Guide](https://docs.aws.amazon.com/ses/latest/dg/send-email-smtp.html)
- [AWS Support](https://console.aws.amazon.com/support/)

