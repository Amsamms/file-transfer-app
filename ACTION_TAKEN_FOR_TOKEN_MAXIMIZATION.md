# OAuth Token Maximization - Actions Taken

This document tracks all actions taken to maximize OAuth token lifetime. If the token gets revoked in the future, start here to understand what was verified and investigate new causes.

---

## Last Verification Date: December 28, 2025

### Token Status at Time of Verification
- **Fresh token generated**: Yes (7:35 AM)
- **App working**: Yes (both local and Streamlit Cloud)

---

## What Was Verified

### 1. Google Cloud Console - OAuth Consent Screen
**URL:** https://console.cloud.google.com/auth/audience?project=work-pc-storage

| Setting | Status | Notes |
|---------|--------|-------|
| Publishing status | ✅ In Production | Not in Testing mode (avoids 7-day expiry) |
| User type | External | Required for personal Gmail accounts |
| OAuth user cap | 1/100 users | Well within limits |

### 2. Google Cloud Console - OAuth Credentials
**URL:** https://console.cloud.google.com/auth/clients?project=work-pc-storage

| Setting | Status | Notes |
|---------|--------|-------|
| Client ID | `318367230698-6uqtpl75r5j6t6vartbl1uib7ist5igu.apps.googleusercontent.com` | Active |
| Client name | Desktop client 1Streamlit File transfer | |
| Type | Desktop | |
| Created | Dec 12, 2025 | |

### 3. Google Cloud Console - Security Checkup
**URL:** https://console.cloud.google.com/auth/overview?project=work-pc-storage

| Check | Status |
|-------|--------|
| Send token securely | ✅ Correctly configured |
| WebViews usage | ✅ Not using WebViews |
| Use secure flows | ✅ Correctly configured |
| Legacy operating systems | ✅ Only modern OS |
| Legacy browsers | ✅ Only modern browsers |
| Billing account | ⚠️ None (optional, doesn't affect token) |
| Project contacts | ⚠️ Needs more owners (optional) |

### 4. Google Account - Third-Party Access
**URL:** https://myaccount.google.com/permissions

| Setting | Status | Notes |
|---------|--------|-------|
| App name | File transfer | Listed in third-party apps |
| Access status | ✅ Active | Not revoked |
| Permission | See, edit, create, and delete all Google Drive files | Full drive access |

### 5. Google Account - Security Settings
**URL:** https://myaccount.google.com/security

| Setting | Value | Impact |
|---------|-------|--------|
| Password last changed | Apr 7, 2021 | ✅ Stable - no recent changes |
| 2-Step Verification | On since Nov 9, 2021 | Normal |
| Enhanced Safe Browsing | On | Normal |

---

## Known Token Revocation Causes

| Cause | How to Check | Status as of Dec 28, 2025 |
|-------|--------------|---------------------------|
| App in Testing mode | Cloud Console → Audience | ✅ In Production |
| Password changed | Security → Password | ✅ Unchanged since Apr 2021 |
| Manual revocation | Google Account → Third-party apps | ✅ Access active |
| 6 months inactivity | N/A - just use app | ⚠️ Use regularly |
| OAuth consent screen modified | Cloud Console → Branding | ✅ No changes |
| Scopes changed | Cloud Console → Data Access | ✅ No changes |

---

## If Token Gets Revoked Again

### Step 1: Check Recent Changes
Ask yourself:
- Did you change your Google password?
- Did you revoke app access in Google Account settings?
- Did you modify anything in Google Cloud Console?
- Has it been more than 6 months since last use?

### Step 2: Check Google Account Security
1. Go to: https://myaccount.google.com/security
2. Look at "Recent security activity"
3. Check if "File transfer" access was removed

### Step 3: Check Google Cloud Console
1. Go to: https://console.cloud.google.com/auth/audience?project=work-pc-storage
2. Verify still in "Production" mode
3. Check OAuth client still exists

### Step 4: Regenerate Token
Follow steps in `SETUP_GUIDE.md` → "How to Regenerate Token"

### Step 5: Update This Document
Add a new section documenting:
- Date of revocation
- Cause identified (if any)
- Actions taken to fix

---

## Token Regeneration History

| Date | Cause | Action Taken |
|------|-------|--------------|
| Dec 28, 2025 | Unknown (possibly 6-month inactivity or consent screen change) | Regenerated token, verified all settings |

---

## Recommendations for Long-Term Token Stability

1. **Never change Google password** unless absolutely necessary
2. **Use the app at least once every 3-4 months** to prevent inactivity revocation
3. **Don't touch Google Cloud Console settings** - leave OAuth consent screen as-is
4. **Don't revoke access** in Google Account → Third-party apps
5. **Don't switch to Testing mode** - keep app in Production

---

## Related Files

- `SETUP_GUIDE.md` - Full OAuth setup and token regeneration guide
- `.streamlit/secrets.toml` - Local secrets (gitignored)
- `token.json` - Local OAuth token (gitignored)
- `client_secret_*.json` - OAuth client credentials (gitignored)
