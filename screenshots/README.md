# Zorro AI Trading Assistant - UI Screenshots

Captured on: August 27, 2026

## Screenshots

### Desktop Views (~1280x800)

1. **ask-desktop.png** - Main Ask/Home page (English, Dark theme)
   - Primary daily chat interface
   - Instrument selector with timeframe buttons (1m, 5m, 5m selected, 1h, 4h, 1d)
   - Model selector: "Sonnet 5 — fast (Quick Scan default)"
   - Analysis type buttons: Quick Scan (active), Deep Analysis, New Analysis
   - Agent Log section
   - Chat composer: "Ask about a catalog instrument..." with Send button
   - Red banner: "Price data unreliable" (backend connection issue during capture)

2. **build-desktop.png** - Build page (English, Dark theme)
   - Three strategy creation cards:
     - "From library" - Versioned Python strategy templates
     - "Convert to bot" - Lock exact levels — no new rules
     - "Draw / describe idea" - Drawings + prose become a draft
   - Footer text: "Mandatory demo before live. Promote-to-live lives on the bot page."

3. **ask-arabic-rtl.png** - Main Ask/Home page (Arabic RTL, Dark theme)
   - Full right-to-left layout
   - Navigation in Arabic: "Zorro", "أسأل" (Ask), "مسح اليوم" (Scan Today), "المزيد" (More)
   - All UI elements properly mirrored and translated
   - Analysis buttons: "مسح سريع" (Quick Scan), "تحليل عميق" (Deep Analysis), "تحليل جديد" (New Analysis)
   - Chat input: "اسأل عن أداة من الكتالوج..." (Ask about a catalog instrument...)

### Mobile Views (~400x924)

4. **ask-mobile.png** - Main Ask/Home page (English, Dark theme, mobile viewport)
   - Responsive mobile layout
   - Bottom navigation bar: Ask (active), Scan Today, Build, More
   - Stacked interface elements optimized for touch
   - All controls accessible and properly sized

## Features Demonstrated

- **Dark Theme**: Professional trading desk aesthetic with dark navy background
- **Multilingual Support**: Full i18n with English, Turkish (Türkçe), and Arabic (العربية) 
- **RTL Layout**: Proper right-to-left support for Arabic UI
- **Responsive Design**: Desktop and mobile viewports
- **Navigation**: Top nav (desktop) and bottom nav bar (mobile)
- **Settings**: Language, Theme, Model defaults, Credentials, Kill switch
- **Analysis Modes**: Quick Scan, Deep Analysis, New Analysis
- **Model Selection**: Sonnet 5 (fast), Fable 5 (strongest)

## Technical Notes

- Frontend: React + Vite + Tailwind CSS
- Backend: FastAPI (Python)
- Charts: KLineCharts library
- i18n: react-i18next
- Mobile: Capacitor for native Android builds

## Capture Environment

- Browser: Chrome on Linux
- Backend: Running but database unavailable (connection refused), so data-dependent pages redirect
- Auth: Temporarily bypassed for screenshot capture
- Pages successfully captured: Ask (home), Build
- Pages requiring DB: Scan Today, Today, Recommendations, etc. (redirect due to 401)

