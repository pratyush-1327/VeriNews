# VeriNews: Streamlined 6-Phase Engineering Plan

A systematic, practical engineering roadmap for **VeriNews**: an AI-powered trusted news reader and real-time misinformation verification platform.

---

## 🎯 Architectural Philosophy & Simplifications

Based on project requirements and scope alignment:
1. **No Authentication / Sign-In Required:**
   - News reading is open and friction-free.
   - Verification requests are submitted directly by users without barriers.
   - Removes complex user management, JWT tokens, password hashing, and login/register screens.
2. **Simplified Geospatial Engine (No GeoAlchemy2 / PostGIS Complexity):**
   - Replaces heavy spatial polygon geometries with a pragmatic 3-tab scope:
     * 🌐 **Global:** International & world affairs.
     * 🇮🇳 **India:** National news.
     * 📍 **City:** Curated for 6 key hubs (**New Delhi**, **Jaipur**, **Mumbai**, **Bengaluru**, **Chennai**, **Kolkata**).
   - The Flutter app checks the device's GPS coordinates via `geolocator`, calculates the closest of the 6 city coordinates, and auto-selects that city tab (with an easy manual city picker dropdown).
   - In SQL, this is indexed with standard `scope` (`global`, `national`, `city`) and `city_tag` (`delhi`, `jaipur`, etc.) string columns.
3. **Laser Focus on Core Academic Value:**
   - **60-word neutral AI summarization** (Gemini 1.5 Flash).
   - **Evidence-based RAG Verification Engine** (atomic claim decomposition, Google Fact Check Tools API, whitelisted web search, NLI truth scoring).
   - **Automated WhatsApp Debunk Card Generator** (Pillow PNG generation).
   - **Native OS Share-Sheet Interception** (Flutter `receive_sharing_intent` from WhatsApp).

---

## 🏗️ Phase 1: Architecture, Data Modeling & Backend Skeleton (Weeks 1–2)
> **Goal:** Set up the monorepo, Docker Compose stack (standard PostgreSQL + Redis + FastAPI), clean relational schemas, and base news/verification API endpoints.

### Key Tasks:
1. **Monorepo Structure Setup:**
   * `/backend`: FastAPI service with Uvicorn.
   * `/mobile`: Flutter client application.
   * `/infra`: `docker-compose.yml` for PostgreSQL 16, Redis 7, and FastAPI.
2. **Database Schema Design (SQLAlchemy 2.0 + Alembic):**
   * `articles` table:
     * `id`: UUID (Primary Key).
     * `title`: String.
     * `summary_60_words`: Text (formatted as 3 concise factual bullets).
     * `source_id`: UUID (Foreign Key to `sources`).
     * `url`: String (unique constraint).
     * `image_url`: String (optional).
     * `published_at`: DateTime.
     * `scope`: Enum (`global`, `national`, `city`).
     * `city_tag`: String (`delhi`, `jaipur`, `mumbai`, `bengaluru`, `chennai`, `kolkata`, or `null`).
     * `created_at`: DateTime.
   * `sources` table:
     * `id`: UUID.
     * `name`: String (e.g., "PIB Fact Check", "The Hindu", "Reuters").
     * `rss_url`: String.
     * `default_scope`: Enum (`global`, `national`, `city`).
     * `default_city_tag`: String (nullable).
     * `credibility_score`: Float (0–100).
     * `is_whitelisted`: Boolean.
   * `verification_dossiers` table:
     * `id`: UUID.
     * `claim_text`: Text.
     * `verdict`: Enum (`TRUE`, `MISLEADING`, `SATIRE`, `FAKE`).
     * `truth_score`: Float (0–100%).
     * `explanation_bullets`: JSON (3 clear bullet points).
     * `evidence_sources`: JSON (list of titles, URLs, and publisher names).
     * `debunk_card_url`: String (path to generated PNG card).
     * `claim_hash`: String (SHA256 for Redis/DB fast lookup).
     * `created_at`: DateTime.
3. **Core API Skeleton:**
   * `GET /api/v1/health`: System health status (verifying PostgreSQL and Redis connectivity).
   * `GET /api/v1/news/feed`: Filterable by `?scope=global`, `?scope=national`, or `?scope=city&city=delhi`.
   * `GET /api/v1/sources`: List whitelisted news and fact-checking sources.
   * `POST /api/v1/verify`: Mock verification endpoint returning structured verdict schema.

**🏁 Milestone Exit Criteria:**
* `docker compose up -d` boots PostgreSQL, Redis, and FastAPI cleanly.
* Alembic migrations run and database tables populate without spatial C-dependency errors.
* Querying `/api/v1/news/feed?scope=city&city=mumbai` returns filtered mock articles in $<20\text{ms}$.

---

## 📰 Phase 2: Trusted News Ingestion & 60-Word AI Summarizer (Weeks 3–5)
> **Goal:** Build the background ingestion pipeline that pulls news from whitelisted RSS feeds, extracts content, summarizes into neutral 60-word briefs, and tags them by scope/city.

### Key Tasks:
1. **Whitelisted RSS Ingestion Engine:**
   * Curate reliable Indian and global RSS feeds:
     * *Global:* Reuters World, BBC International, AP News.
     * *India (National):* The Hindu National, Press Information Bureau (PIB), Indian Express.
     * *City Feeds:* NDTV / Times of India / The Hindu regional feeds for Delhi, Jaipur, Mumbai, Bengaluru, Chennai, Kolkata.
   * Fetch feeds asynchronously using `httpx` and `feedparser`.
   * Extract clean article bodies using `trafilatura` or `newspaper3k`.
   * Deduplicate against existing database records using URL hashing and title normalized matching.
2. **Gemini 1.5 Flash 60-Word Neutral Summarizer:**
   * Build a constrained prompt:
     * Strict length limit: ~60 words.
     * Format: Exactly 3 factual bullet points.
     * Tone: Strictly neutral, journalistic, stripping sensational adjectives and clickbait.
   * Process incoming articles through Google Gemini API.
3. **Scope & City Tagging:**
   * Primary tagging: Assigned automatically based on the source feed's `default_scope` and `default_city_tag`.
   * Fallback entity matching: Simple keyword recognition for the 6 target cities (e.g., "Bengaluru", "Bangalore", "Kempegowda" $\rightarrow$ `bengaluru`).
4. **Automated Ingestion Scheduler:**
   * Run ingestion periodically (every 30 minutes) using lightweight APScheduler or Celery worker.

**🏁 Milestone Exit Criteria:**
* System automatically fetches, summarizes, and categorizes 30+ clean news articles across Global, India, and the 6 cities without manual input.

---

## 🧠 Phase 3: The Evidence-Based RAG Verification Engine (Weeks 6–9)
> **Goal:** Build the multi-step verification pipeline that inspects submitted claims/URLs/images, gathers verified evidence, performs Natural Language Inference (NLI), and generates WhatsApp debunk cards.

### Key Tasks:
1. **Multimodal Claim Ingestion:**
   * `POST /api/v1/verify`: Accepts raw text, article URLs, or image uploads.
   * If URL is provided: Scrape content using `trafilatura` with SSRF protection (blocking internal IP ranges).
   * If Image is provided: Use server-side OCR (Tesseract / Gemini Vision) to extract viral text or screenshot headlines.
2. **Claim Extraction & Search Query Generation (Gemini 1.5 Flash):**
   * Convert messy user text/rumors into an atomic verifiable claim proposition:
     $$\text{Claim} \rightarrow \{\text{Subject}, \text{Assertion}, \text{Temporal/Location Context}\}$$
   * Generate 2–3 targeted web search queries to find debunk reports or original news.
3. **Tri-Layer Evidence Retrieval:**
   * **Layer 1: Google Fact Check Tools API:** Search Google's database of existing accredited debunks adhering to Schema.org `ClaimReview` (from PIB, BoomLive, Quint, AltNews, Snopes).
   * **Layer 2: Live News Search (Tavily / Serper):** Search recent reporting restricted to whitelisted news domains.
   * **Layer 3: Satire Registry:** Match domains against known satire publishers (*The Onion*, *Faking News*, *The Fauxy*).
4. **Natural Language Inference (NLI) & Truth Scoring:**
   * Grounded prompt evaluating mathematical agreement vs. contradiction between Claim and Evidence.
   * Output:
     * **Verdict:** `TRUE`, `MISLEADING`, `SATIRE`, or `FAKE`.
     * **Truth Score:** 0% to 100%.
     * **Summary:** 3 bullet points explaining why the claim is true or false.
     * **Citations:** Clickable titles and URLs of sources used.
5. **WhatsApp-Ready Debunk Card Generator (Pillow / PIL):**
   * Dynamically generate a high-contrast, shareable `1080x1350` PNG image:
     * Color-coded verdict badge (Green for True, Red for Fake, Yellow for Misleading, Purple for Satire).
     * Circular radial Truth Meter graphic.
     * Original claim snippet + 3 factual debunk points.
     * VeriNews watermark & source citations.

**🏁 Milestone Exit Criteria:**
* Run 20 test claims (5 True, 5 Fake, 5 Misleading, 5 Satire); verify that verdicts, citations, and generated debunk PNG images are returned accurately.

---

## 📱 Phase 4: Flutter Cross-Platform Client & OS Share Intent (Weeks 10–12)
> **Goal:** Build the user-friendly Flutter mobile application featuring the 3-tab news reader, location-based city auto-selection, and native WhatsApp share-sheet integration.

### Key Tasks:
1. **Three-Tab News Reader Interface:**
   * Top navigation bar with 3 tabs:
     * 🌐 **Global**
     * 🇮🇳 **India**
     * 📍 **City** (with interactive dropdown to select: *New Delhi, Jaipur, Mumbai, Bengaluru, Chennai, Kolkata*).
   * **Smart Auto-Nearest City Selection:**
     * On first launch, app requests location permission via `geolocator`.
     * Computes the Euclidean/Haversine distance from user's coordinates to the 6 city centers:
       * New Delhi: `(28.6139, 77.2090)`
       * Jaipur: `(26.9124, 75.7873)`
       * Mumbai: `(19.0760, 72.8777)`
       * Bengaluru: `(12.9716, 77.5946)`
       * Chennai: `(13.0827, 80.2707)`
       * Kolkata: `(22.5726, 88.3639)`
     * Automatically sets the City tab to the nearest hub, with instant manual dropdown change.
2. **60-Word Card Layout:**
   * Modern, clean card UI featuring:
     * High typography contrast.
     * 3 bullet summary points.
     * Publisher badge (e.g., "The Hindu • 2h ago").
     * "Read Full Story" external link.
3. **Native OS Share-Sheet Interception:**
   * Configure `receive_sharing_intent` for Android (`AndroidManifest.xml`) and iOS (`Share Extension`).
   * When a user highlights text or a link in WhatsApp or Chrome and taps **"Share to VeriNews"**, the app launches directly into a sleek Verification Modal.
4. **Real-Time Verification Progress Screen:**
   * Live animated progress indicator showing verification stages:
     1. 🔍 *Analyzing claim proposition...*
     2. 🌐 *Checking Google Fact Check registry...*
     3. 📰 *Cross-referencing verified news wires...*
     4. ⚖️ *Computing truth score & generating dossier...*
5. **Dossier Display & One-Tap WhatsApp Debunk Sharing:**
   * Displays the 0–100% Truth Meter, verdict badge, 3 key explanation points, and source citations.
   * **"Share Debunk to WhatsApp"** button: Uses `share_plus` to attach the generated PNG debunk card directly into social chats.
6. **On-Device OCR Preprocessing:**
   * Use `google_mlkit_text_recognition` so screenshots are OCR'd directly on the smartphone, saving bandwidth and backend processing time.

**🏁 Milestone Exit Criteria:**
* You can highlight a viral rumor in WhatsApp, tap *"Share to VeriNews"*, see the animated verification steps, and share the generated PNG debunk card back to WhatsApp in $<5$ seconds.

---

## 🛡️ Phase 5: Redis Claim Caching, Trending Debunks & Admin Portal (Weeks 13–14)
> **Goal:** Protect the backend from duplicate LLM/Search API costs during viral outbreaks, display trending debunks, and provide a lightweight web portal for reviewers.

### Key Tasks:
1. **Semantic Claim Caching (Redis):**
   * During a viral event, thousands of users verify the same text.
   * Normalize claim text (lowercase, strip whitespace, compute SHA-256 hash).
   * Store verified dossiers in Redis with a 24-hour TTL.
   * Subsequent identical requests return the cached dossier instantly ($<30\text{ms}$) with zero LLM API cost.
2. **Public "Trending Misinformation" Feed:**
   * `GET /api/v1/verify/trending`: Displays recently debunked viral claims so users can browse active hoaxes before falling for them.
3. **Fact-Checker / Admin Web Dashboard (Flutter Web / Simple UI):**
   * View feed ingestion logs and source statuses.
   * Add or disable RSS feed URLs.
   * Inspect trending claims and review automated AI verdicts.

**🏁 Milestone Exit Criteria:**
* Cached claim verification returns in $<50\text{ms}$.
* Trending debunks tab displays top viral rumors verified in the last 24 hours.

---

## 🚀 Phase 6: End-to-End Testing, Benchmarking & Viva Preparation (Weeks 15–16)
> **Goal:** Run accuracy benchmarks, package the local demo for viva evaluation, build Android release APK, and finalize the project report.

### Key Tasks:
1. **Evaluation & Benchmarking Suite:**
   * Curate a benchmark dataset of 40 real-world claims (10 True, 10 Fake, 10 Misleading, 10 Satire).
   * Evaluate:
     * Classification Accuracy, Precision, Recall, and F1-score.
     * Latency profile (Cache Hit vs. Cache Miss).
2. **Local Deployment & Live Demo Setup:**
   * Ensure `docker compose up` starts everything on the presenter's laptop with zero external cloud dependencies.
   * Expose the local backend to the mobile phone over local Wi-Fi or free Cloudflare Tunnel (`cloudflared`).
   * Build production-ready Android APK (`flutter build apk --release`).
3. **Project Report & Viva Deliverables:**
   * Complete SRS document, architecture diagrams, and sequence flows.
   * Prepare a 3-minute live demonstration script for examiners (sharing a live hoax from WhatsApp to VeriNews).
   * Prepare slide deck addressing examiner questions on RAG, prompt engineering, and the 6-city routing heuristic.

**🏁 Milestone Exit Criteria:**
* Backend and Flutter app run seamlessly during an end-to-end live test; release APK installed on Android device; final report and presentation slides completed.

---

### Team Task Allocation (For a 4-Person Project Team)

| Role | Primary Responsibilities | Deliverables |
| :--- | :--- | :--- |
| **Member 1 (Backend & Ingestion Lead)** | FastAPI, PostgreSQL, and RSS Ingestion | Database schemas, RSS parsers, 30-min scheduler, news feed endpoints. |
| **Member 2 (AI & Verification Lead)** | Gemini RAG Pipeline & Debunk Generator | Claim decomposition, Fact Check/Search APIs, NLI scoring, Pillow PNG card generator. |
| **Member 3 (Frontend News Lead)** | Flutter News Reader & Geolocation | 3-tab feed UI, 60-word cards, `geolocator` closest city heuristic, city dropdown. |
| **Member 4 (Frontend Integration Lead)** | Share Intent, UI Progress & Testing | Native Android share sheet, verification progress animation, WhatsApp debunk share, evaluation suite. |
