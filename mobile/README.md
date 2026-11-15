# VeriNews Mobile Client (Flutter)

Cross-platform news reader and real-time misinformation verification application.

## Core Features (Phase 4 Deliverables)
1. **Three-Tab Feed Layout:**
   - 🌐 **Global:** International news.
   - 🇮🇳 **India:** National news.
   - 📍 **City:** Local news from 6 target hubs (New Delhi, Jaipur, Mumbai, Bengaluru, Chennai, Kolkata).
2. **Auto-Nearest City Geolocation:**
   - On first launch, queries device location via `geolocator`.
   - Compares user's coordinates with the 6 central coordinates:
     - New Delhi: `(28.6139, 77.2090)`
     - Jaipur: `(26.9124, 75.7873)`
     - Mumbai: `(19.0760, 72.8777)`
     - Bengaluru: `(12.9716, 77.5946)`
     - Chennai: `(13.0827, 80.2707)`
     - Kolkata: `(22.5726, 88.3639)`
   - Auto-selects the nearest city tab, with a dropdown selector for manual switching.
3. **60-Word News Cards:**
   - Factual 3-bullet summaries, source credibility badges, and external full-article links.
4. **Native OS Share Intent:**
   - Receives shared WhatsApp forwards, links, or screenshots via `receive_sharing_intent`.
   - Opens verification modal directly from WhatsApp without manual copy-pasting.
5. **Debunk Sharing:**
   - One-tap WhatsApp debunk card sharing via `share_plus`.
