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

Hugging Face Spaces is chosen because PyTorch requires ~2GB+ RAM, which exceeds Render/Railway free tiers (512MB). Resources vary by HF free tier — verify current limits at https://huggingface.co/pricing before deploying.

> ⚠️ **Free CPU Spaces** may experience cold starts (~10–30s), throttling under load, and occasional container sleeps. Model loading happens once at startup via the `lifespan` handler in `main.py` — ensure your model file is kept reasonably sized (<500MB) to keep startup times acceptable.

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
| `EBIRD_API_KEY` | *(your key — never commit or share this)* |
| `XENO_CANTO_API_KEY` | *(optional — Xeno-Canto may not require auth)* |
| `USE_HYBRID_MODE` | `True` |
| `MODEL_PATH` | `best_bird_model.pth` |

### 1.6 Harden CORS and Verify Backend

Edit `app/main.py` to restrict CORS instead of allowing all origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://birdsg.vercel.app",        # production frontend
        "http://localhost:3000",             # local dev
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Never use `allow_origins=["*"]` in production — it exposes your API to any website.

Also ensure `app/main.py` has the health check endpoint:

```python
@app.get("/health")
def health_check():
    return {"status": "ok"}
```

This is useful for HF deployment debugging, uptime monitoring, and future Android diagnostics.

After deployment, your API will be at:
```
https://YOUR_USERNAME-birdsg-api.hf.space
```

Test: `GET https://YOUR_USERNAME-birdsg-api.hf.space/health`

### 1.7 Add Rate Limiting (Protect Free Tier)

Since your API runs on free hosting, anyone can spam `POST /predict` and consume your HF quota. Add rate limiting to protect against abuse:

Install `slowapi`:

```bash
pip install slowapi
```

Add to `app/main.py`:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi import Request
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

@app.post("/predict")
@limiter.limit("5/minute")  # max 5 uploads per minute per IP
async def predict(request: Request, ...):
    ...
```

This prevents a single IP from flooding your model with requests. Adjust the limit based on expected usage.

---

## Part 2: Database — Supabase Production Config

### 2.1 Create Anon/Public Key (Security Fix)

**Current issue:** `frontend/.env.local` exposes the `service_role` key client-side. This is dangerous — anyone can read/write your entire DB.

1. Go to Supabase Dashboard → Settings → API
2. Copy the **`anon public`** key (NOT the `service_role` key)
3. Replace `SUPABASE_SERVICE_ROLE_KEY` in frontend env with the anon key

### 2.2 Enable Row Level Security (RLS)

**Key principle:** The frontend should **never** write directly to Supabase. All inserts go through FastAPI (which uses the `service_role` key server-side). The frontend only needs read-only access for bird details.

Run these SQL queries in Supabase SQL Editor:

```sql
-- Enable RLS on all tables
ALTER TABLE sightings ENABLE ROW LEVEL SECURITY;
ALTER TABLE bird_species_details ENABLE ROW LEVEL SECURITY;

-- Allow anon users to read bird details (for UI display)
CREATE POLICY "Anyone can read bird details"
ON bird_species_details FOR SELECT
TO anon
USING (true);

-- No anonymous insert policies!
-- Only the service_role key (FastAPI backend) can insert.
-- This prevents bots from flooding your free tier.
```

### 2.3 No Supabase Keys in Frontend

The frontend should have **zero** Supabase keys in its env. The backend (FastAPI) handles all writes via `service_role`, and the frontend reads bird details from FastAPI endpoints, not directly from Supabase.

In `frontend/.env.local`, **remove** all Supabase keys:

```bash
# Remove these — frontend should NOT talk to Supabase directly:
# SUPABASE_SERVICE_ROLE_KEY=...   ← DANGEROUS: full DB access
# NEXT_PUBLIC_SUPABASE_ANON_KEY=... ← Don't need if all reads go through FastAPI
```

The only Supabase key is in the backend's Hugging Face Space secrets (Section 1.5), where it's safe from client-side exposure.

### 2.4 Image Storage Decision

Decide whether to keep uploaded bird photos after inference:

**Option A: Discard images (cheaper, simpler)**
```text
Upload → inference → delete file
```
- Zero storage costs
- Simpler privacy policy (no image retention)
- Cannot revisit past sightings with photos

**Option B: Store in Supabase Storage (richer)**
```text
Upload → inference → save to Supabase Storage → store URL in sightings table
```
- Users can view their past sightings with photos
- Enables future features (gallery, photo review)
- Adds storage costs (~2GB free on Supabase)
- Privacy policy must cover image storage and retention

**Recommendation for v1.0:** Start with Option A (discard). You can add image storage later without breaking the API — the `sightings` table already has an `image_url` column for when you're ready.

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

### 3.2 Vercel Config

No `vercel.json` is needed — Vercel auto-detects Next.js. The default framework preset handles building and deploying correctly. Only create `vercel.json` if you need to override the defaults (e.g., custom install command).

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

6. Click **Deploy**

### 3.5 Verify

Your frontend will be live at:
```
https://birdsg.vercel.app
```

---

## Part 4: Android App with Capacitor (Free)

### 4.1 Install Capacitor + Camera Plugin

```bash
cd frontend

# Install Capacitor
npm install @capacitor/core @capacitor/cli @capacitor/android

# Install camera plugin (needed for bird photo capture)
npm install @capacitor/camera

# Initialize (choose "com.birdsg.app" as app ID)
npx cap init BirdSG com.birdsg.app

# Sync to generate android/ folder with permissions
npx cap sync
```

> `@capacitor/camera` handles required Android permissions automatically. After `npx cap sync`, verify the generated permissions in `android/app/src/main/AndroidManifest.xml` to confirm they match your app's needs.

### 4.2 Configure for Hosted WebView (Recommended)

BirdSG already requires internet (eBird, FastAPI, Supabase), so the APK should load from the Vercel URL rather than bundling the app statically. This gives you a tiny APK, instant frontend updates without app store resubmission, and easier maintenance.

**`frontend/capacitor.config.ts`:**

```typescript
import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.birdsg.app",
  appName: "BirdSG",
  server: {
    url: "https://birdsg.vercel.app",
    cleartext: false,
  },
};

export default config;
```

> **Note:** `next.config.ts` should stay as default (no `output: "export"`). Vercel serves the full Next.js app normally; the Capacitor WebView loads it as a hosted PWA.
>
> **CORS tip:** If testing with Vercel preview deployments (`birdsg-git-main.vercel.app`, `birdsg-pr-*.vercel.app`), add those URLs to `allow_origins` in `app/main.py` as well.

### 4.3 Build and Generate AAB / APK

```bash
# Build Next.js
npm run build

# Sync with Capacitor
npx cap sync

# Open in Android Studio
npx cap open android
```

### 4.4 Set Version and Sign the App

**Step 1 — Bump versionCode / versionName**

Edit `android/app/build.gradle`:
```groovy
android {
    defaultConfig {
        versionCode 1          // increment for each store upload
        versionName "1.0.0"    // user-facing version string
    }
}
```

**Step 2 — Configure signing in Android Studio**

Before you can build a release AAB, you need a keystore:

1. In Android Studio: **Build → Generate Signed Bundle / APK**
2. Select **Android App Bundle**
3. Create new keystore (store password + key password — save these securely!)
4. Select **release** build variant
5. Click **Finish**

This creates the keystore and generates a signed AAB. Android Studio will remember the config for future builds.

Alternatively, build from the command line after signing is configured:

```bash
cd android
./gradlew bundleRelease
```

The signed AAB will be at:
```
android/app/build/outputs/bundle/release/app-release.aab
```

> **Why AAB?** Google Play requires the Android App Bundle (AAB) for new apps since August 2021. AAB is smaller and Play generates optimized APKs per device from it. Note: `./gradlew bundleRelease` builds a release bundle — the result is only signed if signing config is set up in `build.gradle` or done via Android Studio as above.

**Step 3 — Or generate a signed APK (for side-loading / testing)**

In Android Studio:

1. **Build → Generate Signed Bundle / APK**
2. Select **APK**
3. Create new keystore (store password + key password — save these securely!)
4. Select **release** build variant
5. Select signature versions: **V1** and **V2**
6. Click **Finish**

The signed APK will be at:
```
android/app/release/app-release.apk
```

> ⚠️ **Keep your keystore file safe!** You will need it for every future update. If lost, you cannot publish app updates.

### 4.5 Update the App Icon

Replace:
- `frontend/android/app/src/main/res/mipmap-*/ic_launcher.png` — app icon
- Can use a free tool like [Canva](https://canva.com) or [Android Asset Studio](https://romannurik.github.io/AndroidAssetStudio/)

### 4.6 Testing on a Physical Device

Before publishing, test the app on a real Android device:

1. **Enable Developer options** on your phone: Settings → About phone → Tap "Build number" 7 times
2. **Enable USB Debugging**: Settings → Developer options → USB Debugging
3. **Connect phone** via USB to your computer
4. **Run directly** (live reload):
   ```bash
   cd frontend
   npx cap run android
   ```
5. **Or install a signed APK**:
   - Copy `android/app/release/app-release.apk` to your phone
   - Open the file to install (may need to enable "Install from unknown apps")

Verify:
- Camera opens and captures photos
- Bird prediction returns results
- Supabase sightings are recorded (check DB)
- App handles offline / no-network gracefully

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

### 5.4 Upload AAB (Android App Bundle)

1. Go to **Production** → **Create new release**
2. Upload `android/app/build/outputs/bundle/release/app-release.aab`
3. Fill in release notes (e.g., "First release — BirdSG bird identification app")
4. Save and review
5. Roll out production

> Google Play now requires AAB for new apps. The AAB contains all device configurations; Play generates optimized APKs from it for each user's device.

### 5.5 Google Play App Signing

Google Play manages the final signing key automatically:

1. When you upload your signed AAB, Google Play asks you to **opt in to Play App Signing**
2. Your keystore (from Section 4.4) becomes the **upload key** — used only to verify your identity
3. Google Play signs the AAB with its own **app signing key** before distribution
4. **Opt in** — it allows you to reset a lost upload key later (otherwise you'd lose the ability to publish updates)

> ⚠️ Keep your upload keystore + passwords in a secure place (e.g., password manager, encrypted backup). You'll need it for every subsequent release.

### 5.6 App Content

1. Go to **App content**
2. Fill in:
   - **Privacy policy**: URL from privacypolicies.com (see notes below)
   - **Ads**: No
   - **Rating questionnaire**: Fill honestly (Education, Reference)
   - **Target audience**: All ages (or specify)
   - **News apps**: No
   - **COVID-19**: Not related

#### Privacy Policy & Data Safety

Google Play will require you to disclose data collection. BirdSG collects:

| Data Type | Collected? | Purpose |
|-----------|-----------|---------|
| **Photos / Images** | Yes — uploaded by user for bird identification | Core app functionality |
| **Approximate location** | Yes — `lat` / `lng` in sightings | Bird sighting mapping |
| **Device identifiers** | No | — |

Create your privacy policy at https://privacypolicies.com — make sure it explicitly covers image upload and location storage. After submitting, complete the **Data Safety** form in Play Console matching your policy disclosures.

---

## Part 6: Cost Summary

| Item | Cost |
|------|------|
| Hugging Face Spaces (backend) | **$0/mo** — Free tier (resources vary, verify current limits) |
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
| `frontend/next.config.ts` | Keep default — no `output: "export"` (Vercel handles SSR) |
| `frontend/capacitor.config.ts` (new) | Capacitor settings (Hosted WebView mode) |
| `frontend/.env.local` | Remove ALL Supabase keys — frontend reads via FastAPI, not directly |
| `frontend/app/main.py` (delete) | Stray Python file in Next.js app directory — remove before deployment |
| Supabase SQL Editor | Enable RLS + create policies |

---

## Future Improvements

| Area | Suggested Change | Benefit |
|------|-----------------|---------|
| **Merged predict endpoint** | Instead of `POST /predict` then `GET /birds/{label}`, have `POST /predict` return full bird info (common name, scientific name, family, recent sightings) in one response | 1 network call instead of 2, faster mobile UX, less frontend code |
| **Image storage** | Enable Supabase Storage (Section 2.4, Option B) to persist user photos with sightings | Photo gallery, review past IDs, richer app experience |
| **Push notifications** | Add Firebase Cloud Messaging for rare bird alerts | Higher user engagement |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Model fails to load on HF Spaces | Check `MODEL_PATH` env var; model must be committed to repo |
| CORS errors in app | Ensure backend CORS allows your Vercel domain. **Production:** `allow_origins=["https://birdsg.vercel.app"]`. **Dev:** `allow_origins=["http://localhost:3000", "https://birdsg.vercel.app"]`. Never use `["*"]` in production |
| App loads blank page | Check that `server.url` in `capacitor.config.ts` is correct and the Vercel app is accessible |
| Blank / white screen only in Capacitor (works in browser) | Content Security Policy may block inline scripts. Add `server: { cleartext: false }` in `capacitor.config.ts` or configure `android/app/src/main/res/xml/network_security_config.xml` |
| Supabase "permission denied" | Ensure FastAPI backend uses the `service_role` key (frontend has no Supabase access — Section 2.2) |
| APK too large | Use Hosted WebView mode (already the default — ensures tiny APK) |
| "App not installed" on device | Ensure APK is signed (Section 4.4) |
