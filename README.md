# SAAQ — SkillfullyAware Awareness Quotient

AI-powered leadership diagnostic platform by Dr. Mark Pirtle.

Participants complete a reflective survey → Claude AI analyzes responses → a 12-section DOCX diagnostic report is generated with developmental stage assessment, power centers, shadow indicators, and a personalized 90-day growth plan.

## Architecture

```
frontend/          React + Vite + Tailwind (Vercel)
backend/           FastAPI + Python (Render / Railway / Docker)
pipeline/          Node.js DOCX builder + batch processor
docs/              Supabase SQL schema
```

### How it works

```
User fills survey (React) → POST /api/v1/intake/submit
                           → Claude Sonnet analyzes responses
                           → Node.js builds 12-section DOCX
                           → Admin downloads from dashboard
```

### Mobile-ready

The API is fully RESTful JSON — the same endpoints work for React Native, Flutter, or any mobile client. The `frontend/src/api/client.js` can be extracted directly into a mobile app.

## Quick Start (Local Development)

### Prerequisites
- Node.js 18+
- Python 3.11+
- Anthropic API key (get one at console.anthropic.com)

### 1. Clone and configure

```bash
git clone https://github.com/CameronDeb/saaq-finished.git
cd saaq-finished
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 2. Start the backend

```bash
cd backend
pip install -r requirements.txt
cd ..
uvicorn backend.main:app --reload --port 8000
```

### 3. Install pipeline dependencies

```bash
cd pipeline
npm install
cd ..
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the frontend proxies API calls to :8000 automatically.

### 5. Test the pipeline standalone (no API key needed)

```bash
cd pipeline
node build_report.js src/eric_report_data.json output/SAAQReport-Eric.docx
```

## Deployment

### Frontend → Vercel

```bash
cd frontend
vercel --prod
```

Set environment variable in Vercel dashboard:
- `VITE_API_URL` = `https://your-backend-url.com/api/v1`

### Backend → Render / Railway / Docker

Using Docker:
```bash
docker build -t saaq-backend .
docker run -p 8000:8000 --env-file .env saaq-backend
```

Or deploy to Render:
1. Connect the repo
2. Set root directory to `/` (Dockerfile is at root)
3. Add environment variables from `.env.example`

### Database → Supabase (optional)

The backend works with in-memory storage for development. For production:

1. Create a Supabase project
2. Run `docs/supabase_schema.sql` in the SQL Editor
3. Add `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` to `.env`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check + config status |
| GET | `/api/v1/questions/15Q` | Get 15-question survey |
| GET | `/api/v1/questions/29Q` | Get 29-question survey |
| POST | `/api/v1/intake/submit` | Submit survey responses |
| GET | `/api/v1/intakes` | List all submissions (admin) |
| POST | `/api/v1/reports/generate` | Generate report for intake |
| GET | `/api/v1/reports/{intake_id}` | Get report status/data |
| GET | `/api/v1/reports/{intake_id}/download` | Download DOCX |
| GET | `/api/v1/reports` | List all reports (admin) |
| POST | `/api/v1/reports/batch` | Batch generate reports |
| GET | `/api/v1/dashboard` | Dashboard stats |

## Report Sections (12)

1. Title & Introduction
2. Stage Estimate (S1–S10 developmental model)
3. Hemispheric Bias (left/right processing)
4. Power Center Analysis (8 centers)
5. Power Center KPIs (table with baselines + targets)
6. Core Aptitudes (6 dimensions)
7. Shadow Indicators (root → expression → antidote)
8. Somatic Signature Panel
9. Awareness Quotient Summary + HEXACO traits
10. 90-Day Practice Plan (7 subsections)
11. Therapist Handoff Page
12. Appendix (S1–S10 definitions) + QA Table

## Batch Processing

Generate all pilot reports at once:

```bash
# Create a JSON file with respondent data:
# [{"first_name": "Eric", "responses": {"question": "answer", ...}}, ...]

python pipeline/batch_generate.py --data pilot_data.json --output ./output

# Dry run first:
python pipeline/batch_generate.py --data pilot_data.json --dry-run
```

## Cost

Using Claude Sonnet 4.5 ($3/M input, $15/M output):
- ~$0.05 per report
- 18 pilot reports ≈ $1-2
- 100 reports/month ≈ $5-8

## Team

- **Dr. Mark Pirtle** — Product Owner, Framework Author
- **Cameron Deb** — Backend Architecture, Pipeline, Full Stack
