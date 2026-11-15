# VeriNews Mobile Client 📱

A modern Flutter cross-platform client for **VeriNews** built with Google's **Material 3 Extended / Android 17 design language**.

---

## ✨ Features

- **Material 3 Extended Look:**
  - Deep obsidian dark theme (`surfaceContainerLowest`, `surfaceContainerHigh`) and clean canvas light theme.
  - Expressive Google Plus Jakarta Sans typography and pill-shaped chips.
  - Large rounded squircle cards (`BorderRadius.circular(24)`).
  - Verdict-specific tonal glows (`TRUE`, `MISLEADING`, `FAKE`, `SATIRE`, `UNVERIFIED`).

- **3-Segment News Feed:**
  - 🌐 **Global:** Verified international wires (BBC, Al Jazeera).
  - 🇮🇳 **India:** Accredited national coverage (The Hindu, Times of India, NDTV).
  - 📍 **City Hubs:** Geotagged local feeds for 6 cities:
    - New Delhi (`delhi`)
    - Jaipur (`jaipur`)
    - Mumbai (`mumbai`)
    - Bengaluru (`bengaluru`)
    - Chennai (`chennai`)
    - Kolkata (`kolkata`)
  - **Auto-Nearest City Selection:** Calculates GPS distance using the Haversine formula and auto-selects the closest hub, with a quick modal sheet to switch cities.

- **Native OS Share-Sheet Interception:**
  - Registered intent filters in `AndroidManifest.xml` for `text/plain` and `image/*`.
  - When a user highlights a viral WhatsApp forward, tweet, or article and taps **Share to VeriNews**, the app launches immediately into the verification workflow.

- **Real-Time 4-Step Animated Verification Stepper:**
  - 🔍 Step 1: Decomposing atomic claims & queries (Gemini Flash).
  - 🌐 Step 2: Cross-referencing Google Fact Check registry & live news wires (Tavily + DDGS).
  - ⚖️ Step 3: Natural Language Inference veracity scoring.
  - 📊 Step 4: Synthesizing Truth Dossier & dynamic WhatsApp debunk card.

- **Interactive Truth Dossier:**
  - **Radial Truth Meter:** Animated 0–100% circular gauge with score classification.
  - **Color-Coded Verdict Badges:** Distinctive badges for all 5 verdict classes.
  - **Factual Explanation:** 3 clean debunk takeaway bullet points.
  - **Citation Graph:** Accredited source cards with trust scores and direct external links.
  - **Dynamic WhatsApp Debunk Card:** High-contrast 1080x1350 PNG preview with 1-tap **"Share Debunk to WhatsApp"** (`share_plus`).

---

## 🚀 Running the App

### Prerequisites
- Flutter SDK 3.41+
- Dart SDK 3.11+
- VeriNews backend running on port 8000 (`docker compose up -d`)

### Commands
```bash
# Get dependencies
flutter pub get

# Run static analysis
flutter analyze

# Run unit and widget tests
flutter test

# Run app on connected device / emulator
flutter run
```

### Backend Connection Auto-Detection
- **Android Emulator:** Automatically connects to `http://10.0.2.2:8000`.
- **Desktop / Linux / Web:** Automatically connects to `http://localhost:8000`.
- **Physical Device:** Configure host IP in `lib/core/config.dart` or via runtime setting.
