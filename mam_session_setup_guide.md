# MAM Session Setup Guide

## Problem Identified
Your session list shows only **"Short session"** entries. MAM API requires a **long session** with proper configuration.

## Current IP Address
From your session log: `73.161.54.75` (Port 7922)

## Steps to Create Long Session for API Access

### 1. Access Security Settings
- Go to: https://www.myanonamouse.net/preferences/index.php?view=security
- Look for "Create session" section at the bottom

### 2. Configure Long Session
**CRITICAL SETTINGS:**
- ✅ **Check "Allow session to set dynamic seedbox IP"** (REQUIRED for API)
- ✅ **Uncheck "Short session"** (or it will expire quickly)
- Enter IP: `73.161.54.75` 
- Click "Create Session"

### 3. Extract Proper Cookies
After creating the long session:
- Open Developer Tools (F12)
- Go to Application/Storage > Cookies > myanonamouse.net
- Copy BOTH cookies:
  - `mam_id` (long string ~300+ chars)
  - `uid` (your user ID: 193789)

### 4. Expected Result
You should see a new session in your list **WITHOUT** "Short session" label.

## Why Short Sessions Fail
- Short sessions are designed for quick browsing
- They expire within minutes/hours
- API access requires persistent long sessions
- Must have "dynamic seedbox IP" enabled

## Next Steps
1. Create the long session as described above
2. Update your .env file with the new cookies
3. Test the API again

The key is ensuring you create a **long session** with **dynamic seedbox IP** enabled for your current IP address.