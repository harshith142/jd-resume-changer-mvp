# Quick Start: Step-by-Step Automated Workflow

## Installation & Setup

### 1. Load Extension
```
Chrome → Settings → Extensions
Enable "Developer mode" (top right)
"Load unpacked" → Select jd-resume-changer-mvp/extension/
```

### 2. Configure Settings
```
Click extension icon → Settings/Master Resume
Paste your Overleaf master.tex content
Set server URL (default: http://127.0.0.1:8765)
Set GEMINI_API_KEY in terminal
```

### 3. Start Server
```powershell
cd jd-resume-changer-mvp
. .\.venv\Scripts\Activate.ps1
$env:GEMINI_API_KEY = "YOUR_KEY_HERE"
cd server
uvicorn main:app --host 127.0.0.1 --port 8765
```

## Usage: Paste Tab

### Workflow
1. **Copy JD to Clipboard**
   - Open job posting in browser
   - Select and copy entire job description

2. **Paste in Extension**
   - Click extension icon
   - Should be on "Paste JD" tab
   - Paste JD in textarea (Ctrl+V)
   - (Optional) Set target role

3. **Click Generate**
   - Click "Tailor + Compile Resume"
   - Watch progress tracker update through 6 steps
   - Step 4 (Generate LaTeX) will take 3-10 seconds

4. **View Results**
   - Stats show: pages, matched keywords, gaps
   - Changes list AI suggestions
   - ATS notes show optimization tips
   - Download PDF or .tex file

### Example
```
JD Text:
"We're hiring a Senior Java Developer...
Experience with Spring Boot required...
AWS knowledge preferred..."

Step 1: Extract Keywords ✓
↓
Step 2: Load Master Resume ✓
↓
Step 3: Match Keywords ✓
  Found: Java, Spring Boot
  Missing: AWS specifics
↓
Step 4: Generate LaTeX ⊙ (3 seconds...)
↓
Step 5: Compile PDF ✓
↓
Step 6: Validation ✓

Results:
✓ Matched: 18 keywords
✗ Gaps: 3 keywords
📄 Pages: 1
```

## Usage: Upload Tab

### Workflow
1. **Switch to Upload Tab**
   - Click "Upload File" button at top

2. **Select File**
   - Click file input or drag-and-drop
   - Supports: .txt, .docx
   - File must be > 30 characters

3. **Enter Target Role (Optional)**
   - Set role for personalization
   - Example: "Senior Engineer", "ML Engineer"

4. **Click Upload & Process**
   - Same 6-step workflow as Paste
   - File extracted and sent to backend

### Supported Formats

**Plain Text (.txt)**
```
✓ Simple txt files
✓ Copy-pasted text
✓ Notepad documents
✓ Fastest processing
```

**Word Document (.docx)**
```
✓ MS Word files
✓ Google Docs (export as .docx)
✓ Automatically extracts text
✓ Works with complex formatting
```

**PDF (.pdf)**
```
✗ Currently not supported
→ Copy-paste text to .txt file
→ Or use server-side parsing (future)
```

## Understanding Progress Steps

| Step | What It Does | Time |
|------|-------------|------|
| 1. Extract JD Keywords | Parse JD for key skills/requirements | < 1s |
| 2. Load Master Resume | Fetch your base resume from settings | < 1s |
| 3. Match Keywords | Compare JD against your resume | < 1s |
| 4. Generate Tailored LaTeX | Call Gemini AI to tailor content | 3-10s ⭐ |
| 5. Compile to PDF | Run pdflatex compiler | 1-3s |
| 6. Validation Complete | Final checks and result caching | < 1s |

**⭐ Step 4 is the longest** because it's calling an external API (Gemini).

## Interpreting Results

### Keywords Matched vs Gaps

**Matched Keywords (✓)**
- Keywords from JD that appear in your tailored resume
- Higher = better alignment with posting
- Shows your resume is relevant

**Potential Gaps (✗)**
- Keywords from JD not yet in your resume
- Usually skills you don't have or need to emphasize
- Use as guide for future updates

### Changes

**AI Suggestions**
```
Example:
• Added "Microservices architecture" section
• Expanded AWS experience (EC2, Lambda, S3)
• Reorganized projects by relevance to JD
• Enhanced ATS keyword density
```

These are modifications Gemini made automatically.

### ATS Notes

**Formatting & Optimization**
```
Example:
• PDF is one page (meeting standard)
• All keywords naturally integrated
• No formatting blockers detected
• Ready to submit to ATS systems
```

ATS = Applicant Tracking Systems (what companies use to screen resumes).

## Downloading Results

### PDF Download
```
✓ Click [Download PDF]
→ "tailored_resume.pdf" saves to Downloads
→ Ready to email or upload
→ Fully formatted and compiled
```

### LaTeX Download
```
✓ Click [Download .tex]
→ "tailored_resume.tex" saves to Downloads
→ Can import to Overleaf
→ Can edit and recompile locally
```

## Troubleshooting

### Error: "Add your master Overleaf .tex in Settings first"
```
Solution:
1. Click "Settings/Master Resume" link
2. Paste your Overleaf master.tex
3. Click Save
4. Try again
```

### Error: "Paste a complete job description"
```
Reason: JD text is too short (< 30 characters)
Solution:
- Copy entire JD, not just a summary
- Include full requirements and qualifications
- Paste everything
```

### Error: "Server is not running"
```
Reason: Backend server offline
Solution:
1. Terminal: cd jd-resume-changer-mvp/server
2. Run: uvicorn main:app --host 127.0.0.1 --port 8765
3. Wait for "Uvicorn running on http://127.0.0.1:8765"
4. Try again
```

### Error: "Gemini generated malformed LaTeX"
```
Reason: AI output had invalid LaTeX syntax
Solution:
1. This is rare, sanitizer should catch it
2. Just click "Tailor + Compile Resume" again
3. Usually succeeds on retry
4. If persistent: check GEMINI_API_KEY
```

### Error: "PDF is 2+ pages; reduce content/spacing"
```
Reason: Generated resume is too long
Solution:
1. Edit downloaded .tex file
2. Reduce project descriptions
3. Decrease spacing/margins
4. Recompile locally or re-upload
5. Or: Contact Gemini with "fit to one page" prompt
```

### Extension icon shows red "!"
```
Reason: Extension error (usually extension code bug)
Solution:
1. Open DevTools (F12 → extension name)
2. Look for console errors
3. Report error details
```

### File upload says "Unsupported file type"
```
Reason: File format not supported or MIME type wrong
Solution:
- .txt files: Use Windows Notepad, save as .txt
- .docx files: Save from Word/Google Docs as .docx
- .pdf files: Not yet supported, convert to .txt first
- Check file extension in file name
```

## Tips & Best Practices

### 1. Complete Job Descriptions Work Better
```
✓ Good: Full JD with all sections
✗ Avoid: Just bullet points or summary
→ Gemini needs full context
```

### 2. Set Target Role When Relevant
```
Example:
JD: "Senior Java Developer"
→ Set role to "Senior Java Developer"
→ Helps Gemini understand seniority level
```

### 3. Keep Master Resume Updated
```
→ Add recent projects/skills
→ Tailor will be more effective
→ Update every 3-6 months
```

### 4. Download Before Closing Tab
```
✓ Download immediately after processing
→ Results cached in browser
✗ Don't rely on cache across sessions
→ Browser updates may clear local storage
```

### 5. Use Multiple Versions
```
→ Generate versions for different roles
→ Keep tailored_resume_V1, V2, etc.
→ Submit most relevant version
```

## Advanced: Keyboard Shortcuts

| Keys | Action |
|------|--------|
| `Tab` | Switch input focus |
| `Ctrl+V` | Paste from clipboard |
| `Ctrl+A` | Select all text |
| `Ctrl+S` | Save PDF (standard browser) |
| `Enter` | New line in textarea (not submit) |
| `Shift+Enter` | Different action (browser-dependent) |

## Performance Expectations

### Paste Tab
```
Total time: ~5-15 seconds
- Text paste: Instant
- Generation: 3-10 seconds
- Compilation: 1-3 seconds
- Download: < 1 second
```

### Upload Tab (.txt)
```
Total time: ~5-15 seconds
- File reading: < 100ms
- Extraction: Instant
- Generation: 3-10 seconds
- Total: Same as Paste
```

### Upload Tab (.docx)
```
Total time: ~5-15 seconds
- File reading: < 500ms
- DOCX parsing: < 500ms
- Extraction: < 100ms
- Generation: 3-10 seconds
- Total: Same as others
```

**Note:** Generation time depends on Gemini API latency. If network is slow, add 5-10 seconds.

## Next Steps

1. **Master Resume Setup** → Settings page
2. **First Generation** → Paste sample JD or upload
3. **Review Changes** → See Gemini's suggestions
4. **Download PDF** → Use immediately or edit
5. **Repeat** → Generate for multiple JDs
6. **Provide Feedback** → Help improve prompts

## Support

- **Documentation:** See [WORKFLOW.md](WORKFLOW.md) and [ARCHITECTURE.md](ARCHITECTURE.md)
- **Issues:** Check error messages for specific guidance
- **Server Logs:** Terminal shows detailed error messages
- **Extension Logs:** DevTools console (F12)

## Roadmap

Coming soon:
- [ ] Automatic retry on generation failure
- [ ] PDF file upload support
- [ ] Batch generation (5 JDs at once)
- [ ] Resume version comparison
- [ ] LinkedIn URL extraction
- [ ] Keyword ranking by importance

---

**Happy tailoring! 🚀**
