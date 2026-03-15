# 🏗️ App Review Insights Analyser — Detailed Phase-wise Architecture
### Product: Groww | LLM: Groq + Gemini (Free Tier) | Stack: Python + React (Vite)

---

## 📌 Executive Summary

The **App Review Insights Analyser** automatically fetches recent Groww Play Store reviews (using the free, open-source `google-play-scraper`), clusters them into up to 5 key themes using Groq's free LLM API, generates a scannable ≤250-word weekly pulse using Gemini's free API, and sends a draft email to a user-provided address — all triggered from a premium web UI.

**100% Free Stack — no paid APIs required.**

---

## 💸 Free-Tier-Only Technology Stack

| Layer | Technology | Cost | Details |
|-------|-----------|------|---------|
| **Play Store Reviews** | `google-play-scraper` (Python) | ✅ Free | No API key, no login, reads public data |
| **LLM (Themes + Classification)** | Groq `llama3-70b-8192` | ✅ Free tier | 6,000 req/day, 500K tokens/min |
| **LLM (Pulse Generation)** | Google Gemini (`gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-3.1-flash-lite`) | ✅ Free tier | 15 RPM, 1M tokens/min |
| **LLM Clients** | `groq` + `google-generativeai` SDKs | ✅ Free | Official SDKs |
| **Backend API** | FastAPI (Python) | ✅ Free | Async-ready, auto docs |
| **Frontend** | React + Vite | ✅ Free | Fast, modern SPA |
| **Styling** | Vanilla CSS | ✅ Free | Flexible, no framework lock-in |
| **Email** | Gmail SMTP (App Password) | ✅ Free | Needs only a Gmail account |
| **PDF Export** | Browser `window.print()` | ✅ Free | Zero backend dependency |
| **Async Jobs** | FastAPI BackgroundTasks | ✅ Free | No Celery needed for MVP |
| **Data Handling** | pandas, pydantic | ✅ Free | Validation + manipulation |

---

## 🗂️ High-Level System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          USER BROWSER (React UI)                             │
│  ┌────────────────────┐  ┌────────────────────┐  ┌───────────────────────┐  │
│  │  Fetch Live Reviews │  │  View Weekly Pulse  │  │  Enter Email & Send   │  │
│  │                     │  │  (Themes, Quotes,   │  │  Draft Email          │  │
│  └─────────┬──────────┘  │   Action Ideas)     │  └──────────┬────────────┘  │
│            │             └─────────┬───────────┘             │              │
└────────────┼───────────────────────┼─────────────────────────┼──────────────┘
             │  REST API             │                          │
┌────────────▼───────────────────────▼─────────────────────────▼──────────────┐
│                         FASTAPI BACKEND (Python)                             │
│  ┌─────────────────┐  ┌───────────────────┐  ┌──────────────────────────┐   │
│  │ Review Fetcher   │  │ LLM Processing    │  │  Email Draft Service     │   │
│  │ (Play Store      │  │ Groq + Gemini     │  │  (Gmail SMTP, free)     │   │
│  │  Scraper)        │  │ (both free tier)  │  │                          │   │
│  └────────┬────────┘  └─────────┬─────────┘  └──────────┬───────────────┘   │
│           │                     │                        │                   │
│  ┌────────▼─────────────────────▼────────────────────────▼──────────────┐    │
│  │                      Core Pipeline Orchestrator                       │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
             │
┌────────────▼───────────────────────────────────────────────────────────┐
│               EXTERNAL SERVICES (ALL FREE)                               │
│  ┌──────────────┐  ┌──────────────────┐  ┌────────────────────┐          │
│  │  Groq LLM    │  │  Gemini LLM      │  │  Google Play Store │          │
│  │  Free Tier   │  │  Free Tier       │  │  (public reviews)  │          │
│  │  llama3-70b  │  │  gemini-2.5-flash│  │  via scraper lib   │          │
│  └──────────────┘  └──────────────────┘  └────────────────────┘          │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 End-to-End Data Flow

```
User clicks "Fetch Live Reviews"
        │
        ▼
  [Phase 1] Review Fetching & Data Ingestion
        │  - google-play-scraper fetches public Play Store reviews
        │  - Filter: last 8–12 weeks
        │  - Strip PII (usernames, emails, IDs)
        │  - Remove reviews containing emojis
        │  - Deduplicate
        ▼
  [Phase 2] Preprocessing & Enrichment
        │  - Normalise text (lowercase, strip HTML)
        │  - Attach metadata: rating, date
        │  - Chunk reviews into batches (≤50/batch)
        ▼
  [Phase 3] LLM Theme Generation (Groq Free Tier)
        │  - Prompt: "Given these reviews, identify 3–5 themes"
        │  - Parse structured JSON output (theme_name, description)
        │  - Store theme taxonomy
        ▼
  [Phase 4] Review → Theme Classification (Groq Free Tier)
        │  - Prompt: classify each review into one of the N themes
        │  - Assign theme label to each review
        │  - Compute theme frequencies
        ▼
  [Phase 5] Weekly Pulse Generation (Gemini Free Tier)
        │  - Select Top 3 themes by frequency
        │  - Extract 3 representative user quotes (PII-free)
        │  - Generate 3 action ideas
        │  - Produce ≤250-word one-page pulse (Markdown)
        ▼
  [Phase 6] Email Draft Assembly & Send
        │  - Wrap pulse in email HTML template
        │  - Gmail SMTP send to user-supplied address
        ▼
  [Phase 7] UI Display
        - Render pulse in React UI
        - Provide PDF/MD download
        - Show email sent confirmation
```

---

## 📦 Phase-wise Architecture

---

### PHASE 1 — Review Fetching & Data Ingestion

**Goal:** Fetch live reviews from the Google Play Store and produce a clean, PII-free dataset.

#### Data Source: Live Review Fetching

**Primary method:** Fetch reviews directly from Google Play Store using the free `google-play-scraper` Python library.

##### Play Store — `google-play-scraper`

```python
from google_play_scraper import reviews, Sort

result, continuation_token = reviews(
    'com.nextbillion.groww',   # Groww's Play Store package ID
    lang='en',
    country='in',
    sort=Sort.NEWEST,
    count=500,                  # Fetch up to 500 recent reviews
)
# Each review: { score, content, at, thumbsUpCount, ... }
```

**What we get per review:**

| Field | Description | Used? |
|-------|-------------|-------|
| `score` | Rating (1–5) | ✅ Mapped to `rating` |
| `content` | Review text | ✅ Mapped to `text` |
| `at` | Review date (datetime) | ✅ Mapped to `date` |
| `userName` | Reviewer's username | ❌ **Stripped (PII)** |
| `reviewId` | Google's review ID | ❌ **Stripped (PII)** |
| `thumbsUpCount` | Helpful votes | Optional metadata |

> **Note:** App Store support can be added later using `app-store-scraper` if needed. For now, we focus on Play Store reviews only.

#### Components

| Component | Description |
|-----------|-------------|
| `review_fetcher.py` | Calls `google-play-scraper`; returns raw Play Store reviews |
| `pii_scrubber.py` | Regex + rule-based removal of emails, phone numbers, usernames |
| `date_filter.py` | Keeps reviews within the last 8–12 weeks from `run_date` |
| `language_filter.py` | Detects language using `langdetect`; keeps only English reviews |
| `emoji_filter.py` | Removes reviews that contain emoji characters (regex-based Unicode emoji detection) |
| `deduplicator.py` | Drops exact-duplicate review texts |

#### Output Schema (clean_reviews.json)

```json
{
  "id": "rev_001",
  "rating": 4,
  "text": "Love the SIP feature...",
  "date": "2026-01-20",
  "platform": "android"          // hardcoded — Play Store only
}
```

> **PII Rule:** Username, reviewer ID, and any identifiable fields are **never stored**. Title is dropped entirely. Only `rating`, `text`, `date`, and `platform` (hardcoded as `android`) survive ingestion. Platform is limited to **mobile app (Google Play Store) only**.

#### Validation & Filtering Rules
- `rating` ∈ [1, 5]
- `date` parseable as ISO8601
- `text` must have **≥ 5 words** (reviews with fewer words are useless noise — e.g. "good app", "nice")
- `title` field is **dropped entirely** — not stored, not sent to LLM
- **Non-English reviews are removed** using `langdetect` (only `en` reviews pass)
- **Reviews containing emojis are removed** — emoji-heavy reviews tend to be low-signal noise (e.g. "👍👍👍", "🔥🔥 best app"); uses regex-based Unicode emoji detection to identify and drop any review whose `text` contains one or more emoji characters
- Drop rows failing any rule

---

### PHASE 2 — Preprocessing & Text Enrichment

**Goal:** Normalise review text for LLM consumption.

#### Components

| Component | Description |
|-----------|-------------|
| `text_normaliser.py` | Lowercase, strip HTML/markdown, remove special characters |
| `batch_chunker.py` | Groups reviews into batches of 50 for LLM calls |
| `metadata_tagger.py` | Attaches `week_number`, `rating_bucket` (positive/neutral/negative) |

#### Rating Bucketing Logic

```
1–2  → negative
3    → neutral
4–5  → positive
```

#### Output
- `preprocessed_reviews.json` — list of cleaned reviews with metadata
- `review_batches/batch_001.json … batch_N.json`

---

### PHASE 3 — LLM Theme Generation (Groq Free Tier)

**Goal:** Discover 3–5 meaningful themes from the full review corpus.

#### Groq Free Tier Limits
- **Model:** `llama3-70b-8192`
- **Rate limit:** ~6,000 requests/day, 500K tokens/minute
- **Temperature:** 0.2 (deterministic, consistent themes)
- **Max tokens:** 1024
- **Cost:** $0.00

> For ~500 reviews at 50/batch, we make ~10 batch calls for theme extraction + 1 aggregation call = ~11 calls for Phase 3. Well within free tier limits.

#### Approach: All Reviews via Batched Theme Extraction

Since `llama3-70b-8192` has an 8K context window, we can't send all 500 reviews in one call. Instead:

1. **Batch extraction** — Send batches of 50 reviews each to Groq. Each batch returns candidate themes.
2. **Theme aggregation** — Collect all candidate themes from all batches, then make one final Groq call to merge/deduplicate into 3–5 consolidated themes.

This ensures **every single review contributes** to theme identification — no sampling, no reviews left out.

**Step 1: Per-Batch Theme Extraction**

```
You are a product analyst. Below are app reviews for Groww, a stock & mutual fund investing app.

Identify the major themes that appear in these reviews.
Return a JSON array with this structure:
[
  {
    "theme_name": "<short name, max 4 words>",
    "description": "<one sentence describing the theme>",
    "sentiment": "positive|negative|mixed",
    "count": <number of reviews matching this theme in this batch>
  }
]

Rules:
- No PII in descriptions
- Themes must be distinct and non-overlapping

Reviews:
{{batch_reviews}}
```

**Step 2: Theme Aggregation (final call)**

```
You are a product analyst. Below are candidate themes extracted from multiple batches of Groww app reviews.

Merge and consolidate these into exactly 3 to 5 final themes.
Combine similar/overlapping themes. Keep the most representative name and description.
Return a JSON array:
[
  {
    "theme_id": "T1",
    "theme_name": "<short name, max 4 words>",
    "description": "<one sentence describing the theme>",
    "sentiment": "positive|negative|mixed"
  }
]

Rules:
- Max 5 themes
- No PII
- Themes must be distinct

Candidate themes from all batches:
{{all_batch_themes}}
```

#### Output: `themes.json`

```json
[
  {
    "theme_id": "T1",
    "theme_name": "KYC & Onboarding Friction",
    "description": "Users face delays and confusion during KYC verification and account setup.",
    "sentiment": "negative"
  },
  {
    "theme_id": "T2",
    "theme_name": "SIP Management UX",
    "description": "Positive sentiment around ease of setting up and tracking SIPs.",
    "sentiment": "positive"
  }
]
```

#### Error Handling
- Retry up to 3 times on JSON parse failure
- Exponential backoff (1s, 2s, 4s) to respect free tier rate limits
- Fall back to 3-theme minimal set if LLM output is malformed

---

### PHASE 4 — Review → Theme Classification (Groq Free Tier)

**Goal:** Assign each review to its best-matching theme.

#### Approach
- **Method:** Zero-shot classification via Groq
- **Batch size:** 50 reviews/call (to fit context window)
- Sequential API calls with 200ms delay to stay within free tier rate limits

#### Prompt Template

```
Given the following themes:
{{themes_json}}

Classify each review below into exactly one theme_id.
Return a JSON array: [{"review_id": "...", "theme_id": "..."}]

Reviews:
{{batch_reviews}}
```

#### Output: `classified_reviews.json`

```json
[
  {"review_id": "rev_001", "theme_id": "T2"},
  {"review_id": "rev_002", "theme_id": "T1"}
]
```

#### Theme Frequency Table (computed post-classification)

| theme_id | theme_name | count | % share |
|----------|-----------|-------|---------|
| T1 | KYC & Onboarding Friction | 142 | 34% |
| T2 | SIP Management UX | 98 | 23% |

---

### PHASE 5 — Weekly Pulse Generation (Gemini Free Tier)

**Goal:** Produce a scannable ≤250-word weekly note using Google Gemini.

> **Why Gemini for this phase?** Gemini excels at structured, creative writing tasks like generating executive summaries and actionable insights. Using a separate LLM also distributes load across two free-tier APIs, avoiding rate limit pressure on Groq.

#### Gemini Free Tier Limits
- **Models:** `gemini-2.5-flash` · `gemini-2.5-flash-lite` · `gemini-3.1-flash-lite`
- **Rate limit:** 15 RPM, 1,500 RPD, 1M tokens/min
- **Temperature:** 0.3 (balanced creativity + consistency)
- **Cost:** $0.00

#### Sub-components

| Sub-component | Description |
|--------------|-------------|
| `quote_selector.py` | Picks 3 verbatim reviews (1 per top theme); filters PII |
| `pulse_generator.py` | Calls **Gemini** to generate action ideas and summary prose |
| `pulse_formatter.py` | Renders Markdown, enforces 250-word limit |

#### Pulse Prompt Template

```
You are a product insight writer. Write a weekly app review pulse for Groww.

Top 3 Themes (by frequency):
{{top_3_themes}}

User Quotes (do NOT modify):
{{3_quotes}}

Write:
1. A 2-sentence executive summary
2. Brief bullet for each of the 3 themes (1–2 sentences each)
3. 3 actionable improvement ideas for the product team

Rules:
- Total output ≤ 250 words
- No PII (no names, emails, IDs)
- Use clear, simple language
- Format in Markdown
```

#### Output: `weekly_pulse.md`

```markdown
## 📊 Groww Weekly App Review Pulse
**Week of 10 Mar 2026 | 416 reviews analysed**

### Executive Summary
Users appreciate Groww's SIP simplicity but continue to face friction during KYC onboarding.
Support responsiveness remains a concern for 1-star reviews.

### Top Themes
- 🔴 **KYC & Onboarding Friction (34%)** — Verification delays frustrate new users.
- 🟢 **SIP Management UX (23%)** — Easy SIP setup drives strong positive sentiment.
- 🟡 **Customer Support Response (19%)** — Slow ticket resolution cited repeatedly.

### User Voices
> "The KYC got stuck for 3 days with no update — almost gave up on the app."
> "Setting up SIP took less than 2 minutes. Brilliant!"
> "Raised a support ticket 2 weeks ago. Still pending."

### 💡 Action Ideas
1. Add real-time KYC status tracker with estimated completion time.
2. Surface SIP success stories in onboarding to reinforce positive UX.
3. Implement auto-escalation for support tickets older than 72 hours.
```

---

### PHASE 6 — Email Draft Assembly & Delivery

**Goal:** Send the weekly pulse to a user-provided email address via Gmail SMTP (free).

#### Components

| Component | Description |
|-----------|-------------|
| `email_builder.py` | Wraps `weekly_pulse.md` in a responsive HTML email template |
| `email_sender.py` | Gmail SMTP sender using App Password (free, no third-party needed) |
| `email_validator.py` | Basic regex validation of input email |

#### Email HTML Template Structure

```
Subject: 📊 Groww Weekly App Review Pulse — Week of {date}
From:    your-gmail@gmail.com
To:      {user_provided_email}

─────────────────────────────────────
  [Header Banner]
  Weekly App Review Pulse
  Week of 10 Mar 2026
─────────────────────────────────────
  Executive Summary paragraph
─────────────────────────────────────
  Top 3 Themes (styled cards)
─────────────────────────────────────
  User Voices (blockquotes)
─────────────────────────────────────
  Action Ideas (numbered list)
─────────────────────────────────────
  Footer: powered by Groq + Gemini
```

#### Email Config (`.env`)

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SENDER_NAME=Groww Insights Bot
```

> **Gmail App Password Setup:** Settings → Security → 2-Step Verification → App Passwords → Generate. Completely free.

---

### PHASE 7 — React UI (Vite)

**Goal:** A single-page web app to trigger the pipeline and display results.

#### Pages / Views

| View | Description |
|------|-------------|
| **Home** | "Fetch Live Reviews" button; date range selector (8/10/12 weeks) |
| **Processing** | Animated progress stepper (Fetching → Theming → Generating → Ready) |
| **Pulse View** | Rendered weekly pulse with theme cards, quote carousel, action ideas |
| **Email Panel** | Email input field + "Send Draft Email" button + confirmation toast |
| **Download** | Download pulse as `.md` or generate PDF (browser print) |

#### UI Component Tree

```
<App>
 ├── <Navbar>                    — App name, Groww branding
 ├── <ReviewSourcePanel>         — "Fetch Live" button + date range selector
 ├── <ProgressStepper>           — 5-step pipeline progress indicator
 ├── <PulseCard>                 — Executive summary
 ├── <ThemeGrid>                 — 3 theme cards with sentiment badge
 ├── <QuoteCarousel>             — 3 user quotes, cycling animation
 ├── <ActionIdeas>               — 3 numbered action ideas
 ├── <EmailPanel>                — Email input + send button
 └── <DownloadBar>               — MD + PDF download buttons
```

#### API Calls (Frontend → Backend)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/fetch-reviews` | POST | Fetch live reviews via Play Store scraper |
| `/api/run-pipeline` | POST | Trigger full pipeline (theme gen → pulse) |
| `/api/status/{job_id}` | GET | Poll pipeline progress |
| `/api/pulse/{job_id}` | GET | Fetch generated pulse JSON |
| `/api/send-email` | POST | Send email draft with pulse |
| `/api/download/{job_id}` | GET | Download pulse as MD |

---

## 🗄️ Data Storage

```
project-root/
├── data/
│   ├── raw/                    ← Fetched reviews from Play Store
│   ├── processed/
│   │   ├── clean_reviews.json
│   │   ├── preprocessed_reviews.json
│   │   ├── themes.json
│   │   ├── classified_reviews.json
│   │   └── weekly_pulse.md
│   └── exports/
│       └── weekly_pulse_YYYY-MM-DD.md
├── logs/
│   └── pipeline_{job_id}.log
└── temp/                       ← Auto-cleaned after 24h
```

> **Note:** No database needed for MVP. All state is file-based per job. Jobs are identified by `job_id = UUID4`.

---

## 🔑 Security & Privacy

| Concern | Mitigation |
|---------|-----------|
| PII in reviews | `pii_scrubber.py` strips emails, phone numbers, usernames before any LLM call |
| Reviewer usernames | Dropped at ingestion — never stored |
| Email address | Used only for single send; never stored to disk |
| Groq API key | Stored in `.env`; never exposed to frontend |
| Gemini API key | Stored in `.env`; never exposed to frontend |
| SMTP credentials | Stored in `.env`; never logged |
| Review data | Processed in-memory or temp files; purged after 24h |

---

## 📁 Project Directory Structure

```
App Review Insights Analyser/
├── backend/
│   ├── main.py                     ← FastAPI app entry point
│   ├── config.py                   ← Env var loading (.env)
│   ├── routers/
│   │   ├── reviews.py              ← /api/fetch-reviews
│   │   ├── pipeline.py             ← /api/run-pipeline, /api/status
│   │   ├── pulse.py                ← /api/pulse, /api/download
│   │   └── email.py                ← /api/send-email
│   ├── services/
│   │   ├── review_fetcher.py       ← google-play-scraper
│   │   ├── pii_scrubber.py
│   │   ├── date_filter.py
│   │   ├── emoji_filter.py          ← Removes emoji-containing reviews
│   │   ├── deduplicator.py
│   │   ├── text_normaliser.py
│   │   ├── batch_chunker.py
│   │   ├── theme_generator.py      ← Groq: Phase 3
│   │   ├── theme_classifier.py     ← Groq: Phase 4
│   │   ├── pulse_generator.py      ← Gemini: Phase 5
│   │   ├── quote_selector.py
│   │   ├── pulse_formatter.py
│   │   ├── email_builder.py
│   │   └── email_sender.py
│   ├── models/
│   │   ├── review.py               ← Pydantic models
│   │   ├── theme.py
│   │   └── pulse.py
│   ├── utils/
│   │   ├── logger.py
│   │   └── job_store.py            ← In-memory job state
│   ├── data/                       ← Runtime data (gitignored)
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── index.css               ← Design system tokens
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── ReviewSourcePanel.jsx  ← Fetch Live + Date range
│   │   │   ├── ProgressStepper.jsx
│   │   │   ├── PulseCard.jsx
│   │   │   ├── ThemeGrid.jsx
│   │   │   ├── QuoteCarousel.jsx
│   │   │   ├── ActionIdeas.jsx
│   │   │   ├── EmailPanel.jsx
│   │   │   └── DownloadBar.jsx
│   │   └── api/
│   │       └── client.js           ← Axios API wrappers
│   └── package.json
├── data/
│   └── sample_reviews.json         ← Sample output for reference (committed)
├── docs/
│   ├── weekly_pulse_sample.md      ← Latest generated pulse
│   └── email_draft_screenshot.png  ← Email draft screenshot
├── .env.example                    ← Template for credentials
├── ARCHITECTURE.md                 ← This file
└── README.md
```

---

## ⚙️ Pipeline Orchestration (FastAPI BackgroundTasks)

```python
# Simplified orchestration flow in pipeline.py

@router.post("/run-pipeline")
async def run_pipeline(request: PipelineRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid4())
    background_tasks.add_task(execute_pipeline, job_id, request)
    return {"job_id": job_id, "status": "started"}

async def execute_pipeline(job_id: str, request: PipelineRequest):
    # Phase 1 — Fetch from Play Store
    update_status(job_id, "fetching")
    reviews = review_fetcher.fetch(app_id="com.nextbillion.groww", count=500)

    reviews = pii_scrubber.clean(reviews)
    reviews = date_filter.apply(reviews, weeks=request.weeks)
    reviews = emoji_filter.remove(reviews)
    reviews = deduplicator.run(reviews)

    # Phase 2 — Preprocess
    update_status(job_id, "preprocessing")
    reviews = text_normaliser.normalise(reviews)
    batches = batch_chunker.chunk(reviews, batch_size=50)

    # Phase 3 — Theme Generation (Groq)
    update_status(job_id, "generating_themes")
    themes = theme_generator.generate(reviews)

    # Phase 4 — Classification (Groq)
    update_status(job_id, "classifying")
    classified = theme_classifier.classify(batches, themes)

    # Phase 5 — Pulse Generation (Gemini)
    update_status(job_id, "generating_pulse")
    pulse = pulse_generator.generate(classified, themes)     # Gemini call
    pulse_formatter.save(pulse, job_id)

    update_status(job_id, "ready")
```

---

## 🔁 Re-running for a New Week

```
1. Open the UI at http://localhost:5173
2. Click "Fetch Live Reviews" → Reviews from the last 8–12 weeks are fetched automatically
3. Click "Generate Pulse" → The pipeline runs (takes ~30–60 seconds)
4. Review the generated weekly pulse on screen
5. Enter your email → Click "Send Draft Email"
6. (Optional) Download pulse as Markdown / PDF
```

No CLI needed. No manual data export required. Everything is automated via the UI.

---

## 🧪 Testing Strategy

| Test Type | Tool | What Is Tested |
|-----------|------|---------------|
| Unit tests | `pytest` | PII scrubber, date filter, theme parser, text normaliser |
| LLM integration | `pytest` + mock Groq | Theme generation prompt/response parsing |
| API tests | `httpx` + FastAPI TestClient | All REST endpoints |
| Scraper test | `pytest` | `review_fetcher.py` returns valid reviews from Play Store |
| UI smoke test | Manual / Playwright | Fetch → Pulse → Email full flow |
| Email test | Mailtrap sandbox (free) | Email HTML rendering, delivery |

---

## 📊 Theme Legend

| Theme ID | Typical Theme Name | Sentiment | Trigger Keywords |
|----------|--------------------|-----------|----------------|
| T1 | KYC & Onboarding | Negative | kyc, verification, stuck, failed, days |
| T2 | SIP / Investment UX | Positive | sip, invest, mutual fund, portfolio, returns |
| T3 | App Performance | Mixed | crash, slow, lag, update, version |
| T4 | Customer Support | Negative | support, ticket, response, refund, waiting |
| T5 | Features & Wishlist | Mixed | wishlist, add, feature, option, notification |

> Themes are **LLM-generated per run** — the above is illustrative. Actual themes depend on the review corpus.

---

## 🔐 Environment Variables (`.env.example`)

```bash
# Groq (Free Tier — get key at https://console.groq.com)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx

# Gemini (Free Tier — get key at https://aistudio.google.com/apikey)
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX

# Gmail SMTP (Free — generate App Password in Google Account settings)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SENDER_NAME=Groww Insights Bot

# Review Fetching
GROWW_PLAY_STORE_ID=com.nextbillion.groww
DEFAULT_REVIEW_COUNT=500
DEFAULT_WEEKS=12
```

---

## 🚀 Deployment Considerations (Post-MVP)

| Concern | Recommendation |
|---------|---------------|
| Groq free tier rate limits | Add exponential backoff + jitter on retries; ~15 calls/run easily fits |
| Large review sets | Stream reviews in batches; sequential Groq calls with small delays |
| Email delivery | Gmail SMTP works for personal use; SendGrid (free tier: 100 emails/day) for wider use |
| Hosting | Render (free tier) or Railway (free trial) for both frontend + backend |
| Scheduling | GitHub Actions CRON for automated weekly runs (free for public repos) |
| Containerisation | Dockerfile for consistent deployment |

---

## 📅 Phase Execution Timeline

```
Phase 1: Setup + Data Ingestion   — Project init, review fetcher, PII scrubber, data cleaning
Phase 2: Preprocessing            — Text normalisation, batching, metadata tagging
Phase 3: LLM Theme Generation     — Groq integration, theme generation prompts
Phase 4: Theme Classification     — Batch classification, frequency computation
Phase 5: Pulse Generation         — Quote selection, pulse writing, Markdown formatting
Phase 6: Email Delivery           — Gmail SMTP integration, HTML email template
Phase 7: React UI                 — Full frontend with all components, API integration
Final:   Testing & Polish         — End-to-end tests, README, sample data, demo recording
```

---

## 📋 Key Python Dependencies (`requirements.txt`)

```
fastapi==0.115.0
uvicorn==0.30.0
groq==0.11.0
google-generativeai==0.8.0
google-play-scraper==1.2.7
pandas==2.2.0
pydantic==2.6.0
python-dotenv==1.0.0
python-multipart==0.0.9
langdetect==1.0.9
```

All dependencies are **free and open source**.

---

## 📬 GitHub-Based Daily Email Draft Caching

**Goal:** Ensure the expensive LLM-powered review analysis runs **at most once per day**. All subsequent email requests on the same date reuse a cached draft stored in a GitHub repository — no cron jobs, no database, and a free historical archive of daily insights.

### How It Works

```
User enters email → clicks "Send Daily Summary"
        │
        ▼
  ┌─────────────────────────────────────────────────────────┐
  │  Check GitHub repo for /daily-emails/groww_YYYY-MM-DD.txt │
  └──────────────────────────┬──────────────────────────────┘
                             │
              ┌──────────────┼──────────────────┐
              ▼              ▼                   ▼
        [File EXISTS]   [Lock EXISTS]      [Neither EXISTS]
              │              │                   │
              │              │         ┌─────────▼──────────┐
              │              │         │ Create lock file    │
              │              │         │ groww_YYYY-MM-DD    │
              │              │         │ .lock               │
              │              │         └─────────┬──────────┘
              │              │                   │
              │              │         ┌─────────▼──────────┐
              │              │         │ Run full pipeline:  │
              │              │         │ 1. Fetch reviews    │
              │              │         │ 2. LLM themes       │
              │              │         │ 3. Quotes + actions │
              │              │         │ 4. Format draft     │
              │              │         └─────────┬──────────┘
              │              │                   │
              │              │         ┌─────────▼──────────┐
              │              │         │ Save draft (.txt)   │
              │              │         │ to GitHub repo      │
              │              │         │ Delete lock file    │
              │              │         └─────────┬──────────┘
              │              │                   │
              │      ┌───────▼────────┐          │
              │      │ Poll / wait    │          │
              │      │ until .txt     │          │
              │      │ appears        │          │
              │      └───────┬────────┘          │
              │              │                   │
              ▼              ▼                   ▼
        ┌─────────────────────────────────────────────┐
        │  Download draft via GitHub API               │
        │  Send contents as email body to user          │
        └─────────────────────────────────────────────┘
```

### GitHub Repository Structure

```
github-repo/
└── daily-emails/
    ├── groww_2026-03-10.txt      ← Monday's draft
    ├── groww_2026-03-11.txt      ← Tuesday's draft
    ├── groww_2026-03-12.txt      ← Wednesday's draft
    ├── groww_2026-03-13.lock     ← Generation in progress (temporary)
    └── ...                       ← Automatic historical archive
```

- **Draft filename:** `groww_YYYY-MM-DD.txt` (e.g. `groww_2026-03-15.txt`)
- **Lock filename:** `groww_YYYY-MM-DD.lock` (temporary — deleted after generation)

### Components

| Component | Description |
|-----------|-------------|
| `github_cache.py` | Check / read / write / delete files in the GitHub repo via the GitHub Contents API |
| `daily_draft_service.py` | Orchestrates the check → generate → cache → send flow |
| `draft_formatter.py` | Converts the LLM pulse output into a clean plain-text email body |

### Server-Side Logic (Pseudocode)

```python
async def handle_daily_summary(email: str):
    today = date.today().isoformat()                         # "2026-03-15"
    draft_path  = f"daily-emails/groww_{today}.txt"
    lock_path   = f"daily-emails/groww_{today}.lock"

    # 1️⃣ Draft already exists → reuse it
    draft = github_cache.get_file(draft_path)
    if draft:
        send_email(to=email, body=draft)
        return

    # 2️⃣ Lock exists → another request is generating the draft
    if github_cache.file_exists(lock_path):
        draft = await poll_until_ready(draft_path, timeout=120)
        send_email(to=email, body=draft)
        return

    # 3️⃣ Neither exists → we are the first request today
    github_cache.create_file(lock_path, content="generating...")

    try:
        # Run the full pipeline (Phases 1–5)
        reviews = fetch_reviews(app_id="com.nextbillion.groww")
        themes  = groq_theme_generation(reviews)
        classified = groq_classify(reviews, themes)
        pulse   = gemini_generate_pulse(classified, themes)
        draft   = format_as_email_body(pulse)

        # Save draft to GitHub & clean up lock
        github_cache.create_file(draft_path, content=draft)
        github_cache.delete_file(lock_path)
    except Exception:
        github_cache.delete_file(lock_path)                  # Release lock on failure
        raise

    send_email(to=email, body=draft)
```

### GitHub API Usage

All file operations use the **GitHub Contents API** (`repos/{owner}/{repo}/contents/{path}`).

| Operation | API Call | Auth |
|-----------|----------|------|
| Check if file exists | `GET /repos/:owner/:repo/contents/:path` | Personal Access Token |
| Read file contents | Same GET → decode `content` (base64) | Personal Access Token |
| Create / update file | `PUT /repos/:owner/:repo/contents/:path` | Personal Access Token |
| Delete file (lock) | `DELETE /repos/:owner/:repo/contents/:path` | Personal Access Token |

> **Token:** A free GitHub Personal Access Token (classic) with `repo` scope. Stored in `.env` as `GITHUB_TOKEN`.

### Concurrency & Lock Handling

| Scenario | Behaviour |
|----------|-----------|
| First request of the day | Creates lock → runs pipeline → saves draft → deletes lock |
| Subsequent requests (draft exists) | Immediately downloads cached draft — no LLM calls |
| Concurrent request (lock exists) | Polls every 5 seconds for up to 2 minutes until draft appears |
| Pipeline failure | Lock is deleted in `finally` block; next request retries from scratch |
| Stale lock (server crash) | Lock files older than 10 minutes are treated as expired and ignored |

### Environment Variables (additions to `.env`)

```bash
# GitHub Cache (Free — create a Personal Access Token at https://github.com/settings/tokens)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_REPO_OWNER=your-github-username
GITHUB_REPO_NAME=groww-daily-insights
GITHUB_BRANCH=main
```

### API Endpoint

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/daily-summary` | POST | `{ "email": "user@example.com" }` → Check cache → generate if needed → send email |

### Why This Design?

| Benefit | Explanation |
|---------|-------------|
| **No cron jobs** | Generation is triggered on-demand by the first request of the day |
| **No database** | GitHub repo acts as both cache and persistent storage |
| **One analysis/day** | Lock file prevents duplicate LLM runs; subsequent requests reuse the cached draft |
| **Free historical archive** | Every day's draft is permanently stored as a committed file in the repo |
| **100% free** | GitHub API for public/private repos + free LLM tiers |

---

*Generated: 15 March 2026 | Product: Groww | LLMs: Groq llama3-70b-8192 + Gemini (gemini-2.5-flash, gemini-2.5-flash-lite, gemini-3.1-flash-lite) (Both Free Tier) | All APIs: Free*
