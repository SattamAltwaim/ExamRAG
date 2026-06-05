# ExamRAG — AI-Powered Exam Grading System

A Retrieval-Augmented Generation (RAG) system for the Education domain that enables educators to grade student exam papers by comparing answers against course content. The system uses Voyage 3 embeddings, ChromaDB for vector storage, and a Vision Language Model (Claude Sonnet via OpenRouter) to read and grade handwritten/printed exam papers.

## Architecture

```
Exam Image → VLM (extract Q&A) → RAG (retrieve course content) → VLM (grade) → Results
```

- **Embeddings**: Voyage 3 (asymmetric — document/query types)
- **Vector DB**: ChromaDB (persistent, file-based)
- **VLM**: Claude Sonnet 4 via OpenRouter API
- **Backend**: Python FastAPI
- **Frontend**: Static HTML/CSS/JS (Firebase Hosting)
- **Course Content**: 4 PPTX lecture files (GRU, RL, GANs, Generative AI)

## Setup

### 1. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 2. Configure API Keys

Edit `.env` in the project root:

```
VOYAGE_API_KEY=your-voyage-api-key
OPENROUTER_API_KEY=your-openrouter-api-key
```

### 3. Ingest Course Content

```bash
cd backend
python ingest.py
```

This extracts text from all PPTX files in `Content/`, embeds with Voyage 3, and stores in ChromaDB. Takes ~3 minutes due to API rate limits.

### 4. Start Backend Server

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

The server auto-ingests on first startup if ChromaDB is empty.

### 5. Serve Frontend

For local development:

```bash
cd frontend/public
python -m http.server 5500
```

Open `http://localhost:5500` in your browser.

## Usage

1. Open the web app
2. Capture an exam paper via camera or upload an image
3. Optionally select a course topic to narrow the grading context
4. Click "Grade Exam"
5. View per-question scores, feedback, and referenced source slides

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check + document count |
| GET | `/api/courses` | List available course topics |
| POST | `/api/grade` | Grade an exam image |
| POST | `/api/ingest` | Re-run content ingestion |

## Project Structure

```
DL-Project/
├── Content/                  # Course PPTX files
├── backend/
│   ├── main.py               # FastAPI application
│   ├── ingest.py              # Content ingestion pipeline
│   ├── rag.py                 # Vector retrieval logic
│   ├── vlm.py                 # OpenRouter VLM integration
│   ├── config.py              # Configuration
│   └── chroma_store/          # ChromaDB persistent storage
├── frontend/
│   ├── public/
│   │   ├── index.html         # Single-page application
│   │   ├── style.css          # Apple-like dark glass theme
│   │   └── app.js             # Camera capture + API integration
│   └── firebase.json          # Firebase Hosting config
└── .env                       # API keys
```
