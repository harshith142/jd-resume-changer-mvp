```
WORKFLOW DIAGRAM: Step-by-Step Resume Generation
=================================================

┌─────────────────────────────────────────────────────────────────┐
│                    JD Resume Changer Extension                   │
│                                                                   │
│  [Paste JD] [Upload File]  Status: Ready                        │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────┐             │
│  │    PASTE JD TAB      │  │  UPLOAD FILE TAB     │             │
│  │ ─────────────────── │  │ ─────────────────── │             │
│  │ Target role:        │  │ Upload file:        │             │
│  │ [_________]         │  │ [Select file...] ✓  │             │
│  │                     │  │                     │             │
│  │ Job description:    │  │ Target role:        │             │
│  │ ┌─────────────────┐ │  │ [_________]         │             │
│  │ │ Paste JD here.. │ │  │                     │             │
│  │ │ Ctrl + V paste  │ │  │ [Upload & Process]  │             │
│  │ └─────────────────┘ │  └──────────────────────┘             │
│  │                     │                                         │
│  │ [Tailor + Compile]  │                                         │
│  └──────────────────────┘                                         │
│                                                                   │
│  ┌─────────────────────── PROGRESS TRACKER ────────────────────┐ │
│  │ Processing Steps                                             │ │
│  │ ┌──────────────────────────────────────────────────────────┐│ │
│  │ │ ✓ Extract JD Keywords             [done]              ││ │
│  │ │ ✓ Load Master Resume              [done]              ││ │
│  │ │ ✓ Match Keywords                  [done]              ││ │
│  │ │ ⊙ Generate Tailored LaTeX         [generating...]    ││ │
│  │ │ ⏸ Compile to PDF                  [pending]          ││ │
│  │ │ ⏸ Validation Complete             [pending]          ││ │
│  │ └──────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────── RESULTS (After Completion) ─────────────────┐ │
│  │                                                                 │ │
│  │  Stats:  5 Pages    │    42 Keywords Matched    │    8 Gaps   │ │
│  │                                                                 │ │
│  │  Changes:                    ATS Notes:                         │ │
│  │  • Added "Microservices"    • PDF is one page                 │ │
│  │  • Emphasized "AWS"         • All keywords present            │ │
│  │  • Reduced project count    • ATS-optimized formatting        │ │
│  │                                                                 │ │
│  │  [Download PDF]  [Download .tex]                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Settings: Master Resume | Server URL | Help                     │
└─────────────────────────────────────────────────────────────────┘


DATA FLOW: Paste Tab
====================

User Input          Backend                          Output
──────────────      ───────────                      ────────────
JD text     ──┐
Master.tex  ──┼──→ POST /generate ──┬─→ Gemini API
Target role ──┘                     │
              (JSON Request)        │
                                    ├─→ LaTeX Sanitizer
                                    │
                                    ├─→ pdflatex Compiler
                                    │
                                    └─→ Result JSON
                                    
                          ▼
                (Async, ~5-10 sec)
                          ▼
                    Return Data:
                    • latex: "..."
                    • pdf_base64: "..."
                    • page_count: 1
                    • keyword_match: [...]
                    • missing_keywords: [...]
                    • changes: [...]
                    • ats_notes: [...]


DATA FLOW: Upload Tab  (Similar, but extract first)
=======================

User Input          Browser              Backend                Output
──────────────      ────────             ───────────            ────────────
File (DOCX)  ──┐
Target role  ──┼──→ JSZip Extract ──┐
                    XML Parse       │
                    (Instant)       │
                    Get: JD text    │
                                    └──→ POST /generate ──→ Same as Paste
                                         (JSON Request)


STEP STATES & TRANSITIONS
==========================

Initial:  All steps = [pending]  (gray, not started)

During Execution:
  Step 1 → [active] (pulsing blue) → [done] (green)
  Step 2 → [active] (pulsing blue) → [done] (green)
  Step 3 → [active] (pulsing blue) → [done] (green)
  Step 4 → [active] (pulsing blue) → [done] (green)   [longest, API call]
  Step 5 → [active] (pulsing blue) → [done] (green)
  Step 6 → [active] (pulsing blue) → [done] (green)

On Error at Step N:
  Steps 1..N-1: [done] (green)
  Step N: [error] (red)
  Steps N+1..6: [pending] (gray)
  User clicks button again → Reset all → Restart


SUPPORTED FILE FORMATS
======================

Input Method      Supported Formats
─────────────     ─────────────────
Paste Tab         Plain text (any length)

Upload Tab        
  • TXT           Read directly
  • DOCX          Parse via JSZip (word/document.xml)
  • PDF           ❌ Not supported (needs server-side)

All formats validated:
  ✓ File selected
  ✓ Text extracted
  ✓ Length > 30 characters
  ✓ No binary content


ERROR HANDLING FLOW
===================

Try: validate_input()
  ↓
Try: extract_file()  ← File format error
  ↓
Try: POST /generate
  │
  ├─→ 200 OK ──→ render_results()
  │
  ├─→ 422 LaTeX Validation ──→ Show error + retry button
  │
  ├─→ 500 Server Error ──→ Show error + retry button
  │
  └─→ Network Error ──→ Show error + retry button

All errors:
  • Keep completed steps marked [done]
  • Mark current step [error]
  • Re-enable button for retry
  • Display error message
  • Don't lose user input


KEYBOARD & SHORTCUTS
====================

Tab Navigation:
  Tab key → Switch between inputs
  Shift+Tab → Switch backwards

Input:
  Enter (in textarea) → Add line break (not submit)
  Ctrl+A → Select all text
  Ctrl+V → Paste JD from clipboard

Results:
  Ctrl+S → Save PDF (browser standard)
  Ctrl+Click → Open in new tab

Settings:
  Click "Settings" footer link → Options page


BROWSER STORAGE
===============

chrome.storage.local:
  • masterTex: Base Overleaf .tex from settings
  • serverUrl: Backend address (default: http://127.0.0.1:8765)
  • lastResult: Most recent generation output
    - Includes latex, pdf_base64, stats, etc.
    - Persists across extension reloads
    - Used for quick re-download


PERFORMANCE CHARACTERISTICS
============================

Paste Tab:
  - File parsing: Instant (text only)
  - Gemini generation: 3-10 seconds
  - LaTeX compilation: 1-3 seconds
  - Total: ~5-15 seconds

Upload Tab (.txt):
  - File reading: < 100ms
  - Text extraction: Instant
  - Generation: 3-10 seconds
  - Total: ~5-15 seconds

Upload Tab (.docx):
  - File reading: < 200ms (depends on file size)
  - JSZip extraction: < 500ms
  - XML parsing: < 100ms
  - Generation: 3-10 seconds
  - Total: ~5-15 seconds

Step delays (visual effect):
  - Each step shows 300-500ms at [active] before [done]
  - Makes progress visually smooth, not jarring
  - Total overhead: ~2 seconds (adjustable)
```
