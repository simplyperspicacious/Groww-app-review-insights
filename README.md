# App Review Insights Analyser

A lightweight, premium tool designed to fetch live Google Play Store reviews for the Groww app, extract key product themes using LLMs (Groq), and generate structured weekly summaries and action ideas (Gemini). It includes a built-in email dispatch system to deliver insights directly to your inbox.

All core layers operate on 100% free-tier architecture, requiring zero database management and no paid API subscriptions.

---

## Key Features

- **Live Ingestion**: Fetches the most recent 500 reviews directly from the Google Play Store (via google-play-scraper).
- **PII Protection**: Automatically scrubs emails, phone numbers, and identifying handles from review text before any LLM processing.
- **Theme Discovery**: Uses Groq (Llama 3 70B) to identify 3-5 recurring product themes from the fetched review corpus.
- **Pulse Generation**: Leverages Google Gemini to synthesize a scannable weekly pulse report (executive summary, theme frequency, and actionable ideas).
- **Email Delivery**: Integrated SMTP runner that converts the markdown pulse into a premium HTML email and dispatches it via Gmail.
- **Vanilla Web UI**: A minimal, Groww-brand-aligned dashboard built with Vanilla HTML/JS and served by a FastAPI backend.

---

## 7-Phase Architecture

1.  **Ingestion**: Scrape public reviews and strip emojis/PII.
2.  **Preprocessing**: Text normalization and metadata tagging.
3.  **Theme Extraction**: Identifying major user concerns via Groq.
4.  **Classification**: Mapping every review to an identified theme.
5.  **Synthesis**: Generating the pulse report using Gemini.
6.  **Delivery**: Converting reports to HTML and sending via SMTP.
7.  **Web Dashboard**: Unified interface for triggering the pipeline.

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12+, FastAPI, Pydantic, Uvicorn |
| **Frontend** | Vanilla HTML5, CSS3, JavaScript (ES6+), Marked.js |
| **LLM Infrastructure** | Groq (Llama-3-70B), Google Gemini (Flash 1.5 / 2.0) |
| **Data Scraping** | google-play-scraper |
| **Email Service** | SMTP (Standard TLS/SSL) |

---

## Security and Vulnerability Protection

This project is built with security as a priority, especially for cloud deployment on platforms like Render:

- **Zero Database Execution**: The application is stateless. It processes data in-memory and via ephemeral JSON files. There is no database to breach or inject.
- **Strict .gitignore**: Your .env files containing API keys are strictly ignored by Git and never pushed to GitHub.
- **Input Sanitization**: User emails for the dashboard are validated using Pydantic's EmailStr and sanitized before being processed by the SMTP agent.
- **Environment Variables**: The backend is configured to use system environment variables natively. In production (Render), your keys remain encrypted within the platform’s vault and are never exposed to the client-side code.

---

## Local Setup

### 1. Prerequisite Keys
You will need free API keys from:
1.  **Groq Console**: console.groq.com
2.  **Google AI Studio**: aistudio.google.com
3.  **Gmail App Password**: Generated via your Google Account's 2-Step Verification settings.

### 2. Configure Environment
Create a .env file in the root directory (or use .env.example as a template):
```env
GROQ_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 3. Install & Run
```bash
# Setup virtual environment
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m uvicorn main:app --port 8000
```
Open your browser at http://127.0.0.1:8000.

---

## Deployment on Render

This repository is optimized for one-click deployment on Render.com:

1.  **New Web Service**: Connect your GitHub repository.
2.  **Root Directory**: Set to backend/.
3.  **Build Command**: pip install -r requirements.txt.
4.  **Start Command**: uvicorn main:app --host 0.0.0.0 --port $PORT.
5.  **Environment Variables**: Securely add your GROQ_API_KEY, GEMINI_API_KEY, SMTP_USER, and SMTP_PASSWORD in the Render Dashboard's Environment tab.

---

## Directory Structure

```text
├── backend/
│   ├── main.py            # FastAPI Entry Point
│   ├── config.py          # Configuration & Env Loading
│   ├── phase1-6/          # Modular Pipeline phases
│   └── data/processed/    # Ephemeral Data Storage
├── frontend/
│   ├── index.html         # Main Dashboard UI
│   ├── style.css          # Premium Styling (Groww Brand)
│   └── app.js             # API Logic & Dynamic Rendering
├── ARCHITECTURE.md        # Technical Design Specification
└── README.md              # Project Documentation
```
