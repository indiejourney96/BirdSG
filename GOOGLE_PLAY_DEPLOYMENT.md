# BirdSG — Google Play Deployment Guide

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Google Play Store                       │
├──────────────────────────────────────────────────────────┤
│            Capacitor (Native Android Shell)                │
│         ┌──────────────────────────────────────┐          │
│         │  WebView → serves Next.js build      │          │
│         │  (hosted on Vercel OR bundled static) │          │
│         └──────────────┬───────────────────────┘          │
├────────────────────────┼──────────────────────────────────┤
│                        ▼ HTTPS                            │
│  Vercel (Free)         → Next.js Frontend                 │
│  Hugging Face Spaces   → FastAPI + best_bird_model.pth    │
│  Supabase (Free Tier)  → Database + Storage               │
└───────────────────────────────────────────────────────────┘
```

---

## Prerequisites

| Tool | Required? | Cost |
|------|-----------|------|
| Git + GitHub account | Yes | Free |
| Hugging Face account | Yes | Free |
| Vercel account | Yes | Free |
| Supabase account | Already have | Free tier |
| Google Play Developer account | Yes | **$25 one-time** |
| Android Studio | Yes | Free |
| Node.js 20+ | Yes | Free |
| Python 3.11+ | Yes | Free |

---

## Part 1: Backend — FastAPI + Model (Hugging Face Spaces)

Hugging Face Spaces is chosen because PyTorch requires ~2GB+ RAM, which exceeds Render/Railway free tiers (512MB). HF Spaces provides **16GB RAM for free**.

### 1.1 Create Dockerfile

Create `app/Dockerfile.backend` in the project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PyTorch
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY best_bird_model.pth .
COPY species_mapping.json .
COPY bird_details_generated.json .

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

### 1.2 Create Hugging Face Space config

Create `app/README.md` (shown in Space UI):

```markdown
---
title: BirdSG API
emoji: 🐦
colorFrom: green
colorTo: green
sdk: docker
app_port: 7860
---
```

### 1.3 Make model path configurable

Edit `app/model.py` — change line 32 from:

```python
CUSTOM_MODEL_PATH = "best_bird_model.pth"
```

to:

```python
CUSTOM_MODEL_PATH = os.environ.get("MODEL_PATH", "best_bird_model.pth")
```

### 1.4 Deploy to Hugging Face Spaces

```bash
# 1. Create a Space at https://huggingface.co/new-space
#    - Name: birdsg-api
#    - License: apache-2.0
#    - SDK: Docker

# 2. Clone locally and push
cd C:\Users\Admin\Daryl\SD Projects\BirdSG
git init
git add app/ best_bird_model.pth species_mapping.json bird_details_generated.json requirements.txt app/Dockerfile.backend
git commit -m "Initial backend for HF Spaces"

# Add your Space as remote
git remote add space https://huggingface.co/spaces/YOUR_USERNAME/birdsg-api
git push space main
```

### 1.5 Set Environment Secrets

In your Space → Settings → Repository Secrets, add:

| Key | Value |
|-----|-------|
| `SUPABASE_URL` | `https://epiwnjvyrbcihthdibke.supabase.co` |
| `SUPABASE_KEY` | *(your service_role key)* |
| `EBIRD_API_KEY` | `kuuddkvr70pr` |
| `XENO_CANTO_API_KEY` | *(your key)* |
| `USE_HYBRID_MODE` | `True` |
| `MODEL_PATH` | `best_bird_model.pth` |

### 1.6 Verify Backend

After deployment, your API will be at:
```
https://YOUR_USERNAME-birdsg-api.hf.space
```

Test: `GET https://YOUR_USERNAME-birdsg-api.hf.space/health`

---

## Part 2: Database — Supabase Production Config

### 2.1 Create Anon/Public Key (Security Fix)

**Current issue:** `frontend/.env.local` exposes the `service_role` key client-side. This is dangerous — anyone can read/write your entire DB.

1. Go to Supabase Dashboard → Settings → API
2. Copy the **`anon public`** key (NOT the `service_role` key)
3. Replace `SUPABASE_SERVICE_ROLE_KEY` in frontend env with the anon key

### 2.2 Enable Row Level Security (RLS)

Run these SQL queries in Supabase SQL Editor:

```sql
-- Enable RLS
ALTER TABLE sightings ENABLE ROW LEVEL SECURITY;
ALTER TABLE bird_species_details ENABLE ROW LEVEL SECURITY;

-- Allow anon users to insert sightings
CREATE POLICY "Anyone can insert sightings"
ON sightings FOR INSERT
TO anon
WITH CHECK (true);

-- Allow anon users to read sightings
CREATE POLICY "Anyone can read sightings"
ON sightings FOR SELECT
TO anon
USING (true);

-- Allow anon users to read bird details
CREATE POLICY "Anyone can read bird details"
ON bird_species_details FOR SELECT
TO anon
USING (true);
```

### 2.3 Update Frontend Environment

In `frontend/.env.local`, replace with anon key:

```bash
# Before (DANGEROUS):
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# After (safe):
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Part 3: Frontend — Next.js (Vercel)

### 3.1 Make API URL Configurable

**File: `frontend/services/api.ts`** — change to:

```typescript
import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

export default api;
```

**File: `frontend/lib/api.ts`** — change line 1 to:

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
```

### 3.2 Create Vercel Config

Create `frontend/vercel.json`:

```json
{
  "framework": "nextjs",
  "buildCommand": "next build",
  "outputDirectory": ".next",
  "installCommand": "npm install"
}
```

### 3.3 Push to GitHub

```bash
# From the frontend directory
cd frontend
git init
git add .
git commit -m "Initial frontend"
```

Create a GitHub repo (e.g., `birdsg-frontend`) and push:

```bash
git remote add origin https://github.com/YOUR_USERNAME/birdsg-frontend.git
git branch -M main
git push -u origin main
```

### 3.4 Deploy on Vercel

1. Go to https://vercel.com/new
2. Import `birdsg-frontend` repo
3. Framework preset: **Next.js** (auto-detected)
4. Root directory: leave as `./`
5. Environment variables:

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_APP_BASE_URL` | `https://birdsg.vercel.app` |
| `NEXT_PUBLIC_API_URL` | `https://YOUR_USERNAME-birdsg-api.hf.space` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | *(anon public key)* |

6. Click **Deploy**

### 3.5 Verify

Your frontend will be live at:
```
https://birdsg.vercel.app
```

---

## Part 4: Android App with Capacitor (Free)

### 4.1 Install Capacitor

```bash
cd frontend

# Install Capacitor
npm install @capacitor/core @capacitor/cli @capacitor/android

# Initialize (choose "com.birdsg.app" as app ID)
npx cap init BirdSG com.birdsg.app
```

### 4.2 Configure for Static Export (Bundled App)

**Option A: Static export** — the web app is bundled inside the APK (works offline).

**`frontend/next.config.ts`:**

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  images: {
    unoptimized: true,  // required for static export
  },
  trailingSlash: true,
};

export default nextConfig;
```

**Option B: Hosted WebView** — APK loads from Vercel URL (smaller APK, requires internet).

**`frontend/capacitor.config.ts`:**

```typescript
import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.birdsg.app",
  appName: "BirdSG",
  webDir: "out",
  server: {
    url: "https://birdsg.vercel.app",
    cleartext: false,
  },
  bundledWebRuntime: false,
};

export default config;
```

### 4.3 Build and Generate APK

```bash
# Build Next.js
npm run build

# Sync with Capacitor
npx cap sync

# Open in Android Studio
npx cap open android
```

### 4.4 Sign the APK

In Android Studio:

1. **Build → Generate Signed Bundle / APK**
2. Select **APK**
3. Create new keystore (store password + key password — save these!)
4. Select release build variant
5. Select signature versions: **V1** and **V2**
6. Click **Finish**

The signed APK will be at:
```
android/app/release/app-release.apk
```

### 4.5 Update the App Icon

Replace:
- `frontend/android/app/src/main/res/mipmap-*/ic_launcher.png` — app icon
- Can use a free tool like [Canva](https://canva.com) or [Android Asset Studio](https://romannurik.github.io/AndroidAssetStudio/)

---

## Part 5: Google Play Publishing ($25)

### 5.1 Create Developer Account

1. Go to https://play.google.com/console
2. Sign in with a Google account
3. Pay **$25 one-time registration fee**
4. Complete developer profile

### 5.2 Create App Listing

1. Click **Create app**
2. Fill in:
   - **App name**: BirdSG
   - **Default language**: English
   - **App or game**: App
   - **Free or paid**: Free

### 5.3 Fill in Store Listing

| Field | Content |
|-------|---------|
| **Short description** | Identify Singapore birds instantly with AI |
| **Full description** | BirdSG uses advanced AI to identify bird species from photos. Point your camera at any bird and get instant species identification with detailed information about Singapore birds. |
| **Screenshots** | 3-8 phone screenshots (use Android Studio emulator to capture) |
| **Icon** | Use the app launcher icon |
| **Feature graphic** | 1024x500px banner |
| **App category** | Education |
| **Tags** | Bird identification, Singapore, Nature |
| **Privacy policy** | Create free at https://privacypolicies.com |

### 5.4 Upload APK

1. Go to **Production** → **Create new release**
2. Upload `app-release.apk`
3. Fill in release notes (e.g., "First release — BirdSG bird identification app")
4. Save and review
5. Roll out production

### 5.5 App Content

1. Go to **App content**
2. Fill in:
   - **Privacy policy**: URL from privacypolicies.com
   - **Ads**: No
   - **Rating questionnaire**: Fill honestly (Education, Reference)
   - **Target audience**: All ages (or specify)
   - **News apps**: No
   - **COVID-19**: Not related

---

## Part 6: Cost Summary

| Item | Cost |
|------|------|
| Hugging Face Spaces (backend) | **$0/mo** — Free tier (16GB RAM, 2 vCPU) |
| Vercel (frontend) | **$0/mo** — Free tier (100GB bandwidth, 6000 build mins) |
| Supabase (database) | **$0/mo** — Free tier (500MB DB, 5GB bandwidth, 2GB storage) |
| Capacitor (wrapper) | **$0** — Open source MIT license |
| Google Play Developer account | **$25 one-time** |
| Domain (optional) | $0 — Vercel provides `*.vercel.app` |
| **Total first year** | **~$25** |

---

## Appendix: Required Code Changes Checklist

| File | Change |
|------|--------|
| `app/services/api.ts` | `baseURL` → `process.env.NEXT_PUBLIC_API_URL` |
| `app/lib/api.ts` | `API_BASE_URL` → `process.env.NEXT_PUBLIC_API_URL` |
| `app/model.py` | `CUSTOM_MODEL_PATH` → `os.environ.get("MODEL_PATH", ...)` |
| `app/Dockerfile` (new) | Containerize backend |
| `app/README.md` (new) | HF Space config |
| `frontend/next.config.ts` | Add `output: "export"`, `images.unoptimized` |
| `frontend/capacitor.config.ts` (new) | Capacitor settings |
| `frontend/vercel.json` (new) | Vercel build config |
| `frontend/.env.local` | Remove `SUPABASE_SERVICE_ROLE_KEY`, use anon key |
| Supabase SQL Editor | Enable RLS + create policies |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Model fails to load on HF Spaces | Check `MODEL_PATH` env var; model must be committed to repo |
| CORS errors in app | Ensure backend CORS allows your Vercel domain (`allow_origins=["https://birdsg.vercel.app"]`) |
| App loads blank page | Check `webDir` in `capacitor.config.ts` matches build output dir |
| Supabase "permission denied" | Create RLS policies for anon role (Section 2.2) |
| APK too large | Use Option B (hosted WebView) instead of bundling static export |
| "App not installed" on device | Ensure APK is signed (Section 4.4) |
