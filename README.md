# JD Resume Changer

**Chrome MV3 extension + local FastAPI server that tailors your LaTeX résumé to any job description using Gemini AI, then compiles it to PDF locally — keeping your API key and master résumé private.**

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **AI-Powered Tailoring** | Uses Google Gemini to analyze JDs and rewrite your résumé with relevant keywords |
| **Local PDF Compilation** | Runs `pdflatex` on your machine via FastAPI — no cloud compilation |
| **Privacy-First** | Your Gemini API key and master résumé never leave your computer |
| **ATS Optimization** | Improves keyword/semantic alignment and parser-friendly formatting |
| **Keyword Analysis** | Returns structured JSON with matched/missing keywords and suggestions |
| **Chrome Extension (MV3)** | Clean popup UI — paste JD, click Generate, download `.tex` + `.pdf` |

---

## 🏗 Architecture

```
┌─────────────┐     JD + Master .tex      ┌──────────────┐
│  Chrome     │ ────────────────────────▶ │   FastAPI    │
│  Extension  │                           │   Server     │
│  (MV3)      │ ◀─── Tailored .tex + JSON │  (localhost) │
└─────────────┘                           └──────┬───────┘
                                                   │
                                          pdflatex │
                                                   ▼
                                          ┌──────────────┐
                                          │   Your PDF   │
                                          └──────────────┘
```

- **Extension** → Collects JD, sends to local server, downloads results
- **Server** → Calls Gemini, compiles LaTeX, extracts text, validates page count
- **Why local?** Chrome extensions can't safely run `pdflatex`; this keeps your API key out of the extension source

---

## 🛠 Tech Stack

- **Frontend**: Chrome Extension (Manifest V3, vanilla JS)
- **Backend**: FastAPI (Python 3.10+), Uvicorn
- **AI**: Google Gemini API
- **Build**: `pdflatex` (TeX Live / MiKTeX), Poppler (`pdftotext`, `pdfinfo`)
- **Infra**: Docker Compose for easy deployment

---

## 📋 Requirements

- Chrome/Chromium with Manifest V3 support
- Python 3.10+
- A Gemini API key ([Get one here](https://aistudio.google.com/apikey))
- TeX Live / MiKTeX with `pdflatex`
- `pdftotext` and `pdfinfo` (Poppler) — recommended for ATS/page checks

---

## ⚡ Quick Start

### 1. Server

```bash
cd server
python -m venv .venv

# Windows:
.venv\Scripts\activate

# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

Set the Gemini API key:

```bash
# Windows PowerShell:
$env:GEMINI_API_KEY="YOUR_KEY"

# macOS/Linux:
export GEMINI_API_KEY="YOUR_KEY"
```

Start the server:

```bash
uvicorn main:app --host 127.0.0.1 --port 8765
```

### 2. Extension

1. Open `chrome://extensions`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `extension` folder

Open the extension, paste your master Overleaf LaTeX into Settings, then paste a JD and click **Generate**.

> ⚠️ **Recommended**: Use localhost mode where the server owns the Gemini key. Direct mode (key in extension) is not recommended.

---

## 🐳 Docker (Optional)

```bash
docker-compose up --build
```

This starts the server on `http://localhost:8765`.

---

## ⚠️ Important Notes

- **Source of truth**: The master résumé is the single source of truth. Do not let the model invent experience, metrics, employers, dates, degrees, or technologies.
- **ATS optimization** means improving keyword/semantic alignment and parser-friendly formatting; it cannot guarantee a particular ATS score or interview outcome.
- **Privacy**: Your data stays local. The extension only communicates with your localhost server.

---

## 📁 Project Structure

```
jd-resume-changer-mvp/
├── extension/          # Chrome MV3 extension
│   ├── manifest.json
│   ├── popup.html/js
│   ├── background.js
│   └── styles.css
├── server/             # FastAPI backend
│   ├── main.py
│   ├── app/
│   │   ├── api/routes/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   ├── requirements.txt
│   └── Dockerfile
├── web/                # Optional web UI
├── nginx/              # Reverse proxy config
├── docker-compose.yml
└── README.md
```

---

## 🤝 Contributing

PRs welcome! Please read the architecture docs in `ARCHITECTURE.md` and `IMPLEMENTATION.md` first.

---

## 📄 License

MIT License — see `LICENSE` for details.