# Quick Start Guide

Get the Clase Analytics platform running in 5 minutes.

## Prerequisites

- Python 3.8+ 
- Node.js 18+
- A terminal/shell

## 1. Install Dependencies

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

## 2. Start Services

**Terminal 1 — Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
# Should output: "Uvicorn running on http://0.0.0.0:8000"
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
# Should output: "▲ Next.js 14.0.0 ready on http://localhost:3000"
```

## 3. Access the Application

Open your browser to: **http://localhost:3000**

You should see the Clase Analytics home page with one example session from March 31, 2026.

## 4. Explore the Features

1. **View Session** — Click on the March 31 session card
2. **Overview Dashboard** — See KPIs, participation charts, and quality distribution
3. **View Transcription** — Search and filter by speaker
4. **Check Participation** — See student questions with quality ratings
5. **Review Evaluation** — View A-E evaluation framework
6. **Manage Speakers** — Edit speaker names and information
7. **Create New Class** — Click "+ New Class" to start the wizard (step 4 is a demo)

## 5. Key Pages

| URL | Purpose |
|-----|---------|
| `/clases` | Session selector (landing page) |
| `/clases/2026-03-31` | Session overview |
| `/clases/2026-03-31/transcripcion` | Full transcript with search |
| `/clases/2026-03-31/participacion` | Questions and responses |
| `/clases/2026-03-31/evaluacion` | Evaluation frameworks |
| `/clases/2026-03-31/hablantes` | Speaker profiles |
| `/clases/crear` | Create new class (4-step wizard) |

## 6. Edit Speaker Names

1. Go to `/clases/2026-03-31/hablantes`
2. Click "Edit Info" on any student
3. Fill in: Name, Degree (PhD/Master/Other), Nationality, Email
4. Click "Done" to save

Changes are persisted in `/data/clases/2026-03-31/speakers.json`

## 7. Customize the Data

All session data is stored as JSON in `/data/clases/{date}/`

- `metadata.json` — Session info and statistics
- `speakers.json` — Speaker profiles (edit student names here)
- `analysis.json` — Complete analysis (transcription, questions, evaluation frameworks)

Edit these files directly to customize the data.

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process if needed and try again
```

### Frontend shows "connection refused"
- Make sure backend is running on `http://localhost:8000`
- Check that FastAPI startup message appears
- Try refreshing the browser page

### No session appears
- Check that `/data/clases/2026-03-31/metadata.json` exists
- Verify the backend is serving API responses: visit `http://localhost:8000/api/clases`

### Styling issues
```bash
cd frontend
npm install  # Re-install dependencies
npm run dev  # Restart dev server
```

## Next Steps

1. **Create more sessions** — Use the "+ New Class" wizard
2. **Integrate audio processing** — Connect to Gemini/Whisper APIs
3. **Deploy to cloud** — See deployment guides in project documentation
4. **Customize evaluation** — Modify frameworks in `/data/clases/{date}/analysis.json`

## File Locations

```
/Users/santi/clase-analytics/
├── backend/main.py          # FastAPI server
├── frontend/src/app/        # Next.js pages
└── data/clases/             # Session data
    └── 2026-03-31/          # Example session
        ├── metadata.json
        ├── speakers.json
        └── analysis.json
```

## Need Help?

Check the README.md for detailed documentation on all features and API endpoints.
