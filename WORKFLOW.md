# Step-by-Step Workflow: JD Resume Changer

## Overview

The JD Resume Changer now supports two automated workflows for generating tailored resumes:

1. **Paste JD Tab** - Paste job description text directly
2. **Upload File Tab** - Upload JD as a file (TXT, DOCX)

Both workflows execute the same 6-step pipeline with real-time progress tracking.

## Workflow Steps

### Step 1: Extract JD Keywords
- Parses the job description to identify key requirements
- Extracts technical skills, soft skills, and domain knowledge
- Sets baseline for matching against your resume

### Step 2: Load Master Resume
- Retrieves your master LaTeX resume from settings
- Validates document structure and availability
- Prepares for tailoring operations

### Step 3: Match Keywords
- Compares JD keywords against master resume content
- Identifies skills you already have
- Flags gaps where you could strengthen the application
- Shows matched vs. missing keywords in results

### Step 4: Generate Tailored LaTeX
- Calls Gemini AI to create tailored LaTeX
- Incorporates matched keywords naturally
- Maintains ATS-friendly formatting
- Validates output with comprehensive LaTeX sanitizer

### Step 5: Compile to PDF
- Invokes pdflatex compiler on validated LaTeX
- Generates production-ready PDF
- Validates multi-page compliance (targets 1-page)
- Captures compilation log for debugging

### Step 6: Validation Complete
- Final safety checks
- Ensures PDF generation succeeded
- Stores result in browser cache
- Ready for download

## User Interface

### Tab Switching
```
[Paste JD] [Upload File]
```
- Switch between input methods without losing data
- Each tab maintains its own state

### Progress Display
```
Extract JD Keywords      ✓ done
Load Master Resume       ✓ done
Match Keywords           ✓ done
Generate Tailored LaTeX  ⊙ generating...
Compile to PDF           ⏸ pending
Validation Complete      ⏸ pending
```

Status indicators:
- **pending** (gray) - Not started
- **generating...** (blue, pulsing) - Currently processing
- **done** (green) - Completed successfully
- **failed** (red) - Error occurred

### Results Section
After successful processing:
- **Pages**: PDF page count
- **Keywords matched**: Number of JD keywords found in tailored resume
- **Potential gaps**: Keywords from JD not yet in resume
- **Changes**: AI-suggested modifications
- **ATS notes**: Formatting and keyword optimization tips
- **Download buttons**: Export PDF or .tex file

## File Upload Support

### Supported Formats
- **TXT** - Plain text files
- **DOCX** - Microsoft Word documents (parsed via JSZip)
- **PDF** - Not currently supported (requires server-side parsing)

### File Selection
1. Click "Upload File" tab
2. Click file input area or drag-and-drop
3. Select a JD file from your computer
4. (Optional) Enter target role for context
5. Click "Upload & Process"

## Error Handling

### Step Failure
If any step fails:
- All completed steps remain marked "done"
- Failed step marked "failed" with error reason
- Subsequent steps stay "pending"
- Error message displayed in status bar
- Button re-enabled for retry

### Common Errors
- **"Add your master Overleaf .tex in Settings first"** → Configure master resume in Options
- **"File contains less than 30 characters"** → Job description too short
- **"Generation failed"** → Check server is running and API key configured
- **"Gemini generated malformed LaTeX"** → Sanitizer caught invalid output (retry usually works)

## Advanced Features

### Keyword Matching Logic
- Case-insensitive matching
- Exact substring search in LaTeX
- Identifies which keywords are already present
- Suggests which missing keywords to prioritize

### ATS Optimization
- Validates resume formatting for Applicant Tracking Systems
- Checks for common ATS blockers
- Flags page count issues
- Suggests spacing/content adjustments

### Automatic Repair
If LaTeX sanitizer rejects Gemini output:
- Error detail includes specific validation failures
- Server returns 422 status with structured error
- Future: Automatic Gemini re-prompting with failure details

## Settings (Options Page)

Required configuration:
- **Master Resume .tex** - Your base Overleaf resume LaTeX code
- **Server URL** - Backend server address (default: http://127.0.0.1:8765)
- **Gemini API Key** - Set in environment (GEMINI_API_KEY)

## Data Privacy

- All processing runs locally or on your server
- JD text and resume are sent only to your backend
- Backend communicates with Gemini API (configured via API key)
- PDF and LaTeX results stored in browser's local storage
- Results cached for quick re-download

## Keyboard Shortcuts

- **Tab** - Switch between Paste and Upload tabs
- **Enter** (in textarea) - Alt+Enter for new line; send requires button click
- **Ctrl+S** - (After completion) Standard browser save for PDF

## Future Enhancements

- [ ] Automatic Gemini re-prompting on validation failure
- [ ] Direct PDF upload support (via server-side parsing)
- [ ] Batch resume generation for multiple JDs
- [ ] Keyword ranking by importance
- [ ] LinkedIn URL extraction from JD
- [ ] Resume version comparison (before/after diff)
- [ ] Custom sanitizer rules
- [ ] Multi-language support
