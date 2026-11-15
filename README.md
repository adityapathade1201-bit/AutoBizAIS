# AutoBiz AI — AI-Powered Business Platform for Indian SMEs

A modern, professional web application prototype featuring AI-driven agents, business analytics, and a WhatsApp-inspired chat interface.

## Quick Start

```bash
cd AutoBizAI
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

## Project Structure

```
src/
├── App.tsx                  # Root with all routes
├── main.tsx                 # Entry point
├── index.css                # Design system (Tailwind layers, custom components)
├── types/index.ts           # TypeScript interfaces
├── services/api.ts          # API service layer
├── services/config.ts       # Shared HTTP and WebSocket endpoint configuration
├── stores/
│   ├── agentStore.ts        # Zustand: agents & chat state
│   └── appStore.ts          # Zustand: theme, language, sidebar
├── layouts/
│   └── AppLayout.tsx        # App shell with nav (desktop sidebar + mobile bottom)
├── pages/
│   ├── Welcome.tsx          # Landing page
│   ├── onboarding/
│   └── app/                 # Agents, analytics, marketplace and dashboard
public/
└── data/                    # Bundled demo data and local fallbacks
```

## Backend Setup (Required for Real AI Replies)

The frontend and FastAPI backend are separate processes. The Android app does not bundle or start the Python backend. Do not use a temporary Ngrok URL as the permanent mobile endpoint.

### Run locally

1. Create `backend/.env` and add `OPENROUTER_API_KEY=your_real_key` (never commit this file).
2. Install backend dependencies: `cd backend && python -m pip install -r requirements.txt`.
3. Start the backend: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`.
4. In another terminal at the project root, copy `.env.example` to `.env.local` and keep `VITE_API_BASE=http://localhost:8000/api`.
5. Run `npm install` and `npm run dev`.

### Deploy the backend for a physical Android phone

1. Push this repository to GitHub and create a Render Blueprint using the included `render.yaml`.
2. In the Render service settings, set the secret `OPENROUTER_API_KEY`. Do not put the key in frontend variables or source code.
3. Wait for the service to become healthy. Test its root URL; it should return the AutoBiz AI backend status JSON.
4. Set `VITE_API_BASE` to `https://YOUR-BACKEND.onrender.com/api` in the frontend build environment. For a local Android build, set it in `.env.production.local` (this file is ignored by Git).
5. Build and sync the Android app from the project root:

   ```bash
   npm install
   npm run build
   npx cap sync android
   npx cap open android
   ```

6. Build/install the APK from Android Studio. Rebuild and sync the app whenever the backend URL changes because Vite embeds this value at build time.

The HTTP API and WebSocket now derive their destinations from the same `VITE_API_BASE`. Local browser development defaults to `http://localhost:8000/api`; a physical Android app requires a publicly reachable HTTPS backend URL. Chat failures are shown as real errors instead of fake successful replies.

**Storage warning:** This backend currently stores conversation memory and business facts in local JSON files under `backend/data`. A free cloud instance may have an ephemeral filesystem, so do not use it for important or customer data without adding durable storage (a persistent disk or database).

## Tech Stack

| Layer         | Technology                              |
|---------------|----------------------------------------|
| Framework     | React + TypeScript                     |
| Styling       | Tailwind CSS                           |
| State         | Zustand                               |
| Charts        | Recharts                               |
| Icons         | Lucide React                           |
| Routing       | React Router                           |
| Build         | Vite                                   |

## Routes

| Path                  | Description              |
|-----------------------|--------------------------|
| `/welcome`           | Landing page             |
| `/onboarding/guided` | Guided onboarding        |
| `/onboarding/freetext` | Free-text business input |
| `/onboarding/upload` | Document upload          |
| `/onboarding/analyzing` | Loading animation     |
| `/onboarding/results` | AI analysis results      |
| `/app/agents`         | Agent chat                |
| `/app/business`       | Analytics dashboard       |
| `/app/community`      | Agent marketplace         |
| `/app/dashboard`      | Settings and controls     |

## Features

- 🌙 Dark/Light theme toggle
- 🌐 English/Hindi language switch
- 📱 Mobile-first responsive design
- 💬 WhatsApp-inspired agent chat
- 📊 Interactive business charts
- 🤖 Agent marketplace
- 🇮🇳 Built for Indian SMEs (₹ currency, local industries)

## Building for Production

```bash
npm run build
```

Output goes to `dist/`. Deploy the static frontend to any hosting provider and set `VITE_API_BASE` in that provider's build environment.
