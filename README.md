# Comp3000 - Terms of Service Comprehension Study Platform

A research platform that measures how different presentation formats affect user reading behaviour and comprehension of Terms of Service documents. Six presentation conditions are tested, ranging from plain text through to AI-enhanced interactive layouts, with eye-tracking, scroll analytics, and comprehension assessments collected throughout.

**Author:** Alexander Trzcinski-Draper  
**Supervisor:** Dr Haoyi Wang, University of Plymouth  
**Module:** COMP3000 Computing Project (BSc Computer Science, 2025/26)

---

## Project Structure

```
Main/
  backend/
    NLP/              Python/FastAPI backend service
    tobii/            Tobii Research SDK (Python bindings, unmodified)
    tobii_native/     Tobii Stream Engine native library (unmodified)
  frontend/           Angular 21 single-page application
```

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| Node.js | 20+ |
| npm | 10+ |
| Tobii EyeX | Optional - study runs without it |

> **Tobii Calibration:** This study was conducted using a Tobii EyeX, but any Tobii eye tracker should work. Before running the study with eye-tracking, install and run the calibration software for your specific device. For the EyeX, use the [Tobii Experience / Core Software](https://gaming.tobii.com/getstarted/?bundle=tobii-core). For other devices, download the software from the [Tobii website](https://gaming.tobii.com/getstarted/). Without calibration, gaze data will be inaccurate. Eye-tracking is automatically skipped if no device is detected.

> **Note:** The study was conducted on a 1440p (2560x1440) monitor. Layout dimensions and gaze coordinate mappings are calibrated for this resolution. If running on a different display, update `SCREEN_W` and `SCREEN_H` in `Main/backend/NLP/gaze_utils.py` - all visualisation scripts import these values from there.

---

## Backend Setup

```bash
cd Main/backend/NLP  # (cd backend/NLP if in VS Code)
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

The API server starts on `http://localhost:8000`.

On first run, a SQLite database (`tos_research.db`) is created automatically. If no Tobii EyeX device is detected, eye-tracking is silently disabled and all other functionality continues normally.

### Backend environment

All dependencies are listed in `Main/backend/NLP/requirements.txt`. Key packages include FastAPI, Uvicorn, PyTorch, Hugging Face Transformers, Sumy (extractive summarisation), YAKE (keyword extraction), Matplotlib, and Playwright.

---

## Frontend Setup

```bash
cd Main/frontend  # (cd frontend if in VS Code)
npm install
npm start
```

The development server starts on `http://localhost:4200` and proxies API calls to the backend.

### Available scripts

| Command | Description |
|---------|-------------|
| `npm start` | Start development server |
| `npm run build` | Production build |
| `npm test` | Run tests in watch mode |
| `npm run test:run` | Run tests once |
| `npm run lint` | Run ESLint |
| `npm run serve:ssr:frontend` | Serve the SSR production build |

---

## Study Design

Six presentation conditions are presented to each participant, one per Terms of Service document:

| Condition | Description |
|-----------|-------------|
| C1 - Plain Text | Unformatted raw ToS |
| C2 - Scroll-Gated | Participant must scroll to the bottom before proceeding |
| C3 - Formatted | Structured layout with headings and visual hierarchy |
| C4 - AI Summary | Extractive summary shown alongside the document |
| C5 - AI Enhanced | Inline AI annotations highlighting risk clauses |
| C6 - AI Hover | AI-generated explanations revealed on hover |

Between each ToS document, a distractor task is shown (word scramble, pattern match, math quiz, reaction time, or spot the difference) to reset working memory.

A comprehension test is completed at the end of the session.

---

## Data Collection

The following data is recorded per session:

- Scroll events: position, depth, direction, and timestamps
- Pause events: scroll depth and duration of stationary periods
- Hover events: clause category and dwell time
- Gaze samples: normalised (x, y) coordinates and validity flags (Tobii EyeX)
- Session metadata: reading time, scroll depth reached, condition group, risk score
- Comprehension test results: per-condition scores and self-reported confidence ratings

All data is stored locally in `tos_research.db` (SQLite). Participant names are anonymised as P01-P10.

---

## Running Tests

**Backend:**
```bash
cd Main/backend/NLP  # (cd backend/NLP if in VS Code)
pytest
```

**Frontend:**
```bash
cd Main/frontend  # (cd frontend if in VS Code)
npm run test:run
```

---

## Visualisations

Pre-built visualisation scripts are located in `Main/backend/NLP/dissertation_figures/`. They read from `tos_research.db` and output charts to `Main/backend/NLP/output/dissertation/`.

Eye-tracking visualisations (heatmaps, scanpaths, AOI overlays, fixation bubbles) are generated via the scripts in `Main/backend/NLP/visualisations/`.

```bash
cd Main/backend/NLP  # (cd backend/NLP if in VS Code)
python generate_visualisations.py
python generate_dissertation_figures.py
```
