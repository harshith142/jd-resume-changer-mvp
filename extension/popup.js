const $ = id => document.getElementById(id);
let latest = null;

// ============================================================
// TAB SWITCHING
// ============================================================
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", e => {
    const tab = e.target.dataset.tab;
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    e.target.classList.add("active");
    $(`${tab}-tab`).classList.add("active");
  });
});

// ============================================================
// STEP TRACKING
// ============================================================
function markStep(stepNum, status, message) {
  const step = $(`step-${stepNum}`);
  step.classList.remove("pending", "active", "done", "error");
  step.classList.add(status);
  const statusEl = step.querySelector(".step-status");
  statusEl.textContent = message || status;
}

function resetSteps() {
  for (let i = 1; i <= 6; i++) {
    const step = $(`step-${i}`);
    step.classList.remove("active", "done", "error");
    step.querySelector(".step-status").textContent = "pending";
  }
}

// ============================================================
// PASTE TAB - EXISTING FLOW
// ============================================================
async function load() {
  const data = await chrome.storage.local.get(["lastResult"]);
  if (data.lastResult) {
    latest = data.lastResult;
    render(latest);
  }
}
load();

$("generate").addEventListener("click", async () => {
  $("status").textContent = "Generating...";
  $("generate").disabled = true;
  $("progress").hidden = false;
  resetSteps();

  try {
    const settings = await chrome.storage.local.get(["masterTex", "serverUrl"]);
    if (!settings.masterTex) throw new Error("Add your master Overleaf .tex in Settings first.");

    const jd = $("jd").value.trim();
    if (jd.length < 30) throw new Error("Paste a complete job description.");

    markStep(1, "active", "extracting...");
    await new Promise(r => setTimeout(r, 500));
    markStep(1, "done", "extracted");

    markStep(2, "active", "loading...");
    await new Promise(r => setTimeout(r, 500));
    markStep(2, "done", "loaded");

    markStep(3, "active", "matching...");
    await new Promise(r => setTimeout(r, 500));
    markStep(3, "done", "matched");

    markStep(4, "active", "generating...");
    const base = settings.serverUrl || "http://127.0.0.1:8765";
    const r = await fetch(base + "/generate", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        jd,
        master_tex: settings.masterTex,
        target_role: $("role").value.trim()
      })
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail?.message || data.detail || "Generation failed.");
    markStep(4, "done", "generated");

    markStep(5, "active", "compiling...");
    await new Promise(r => setTimeout(r, 500));
    markStep(5, "done", "compiled");

    markStep(6, "active", "validating...");
    await new Promise(r => setTimeout(r, 500));
    markStep(6, "done", "complete");

    latest = data;
    await chrome.storage.local.set({lastResult: data});
    render(latest);
    $("status").textContent = "Done";
  } catch (e) {
    $("status").textContent = e.message;
    let markedError = false;
    for (let i = 1; i <= 6; i++) {
      const step = $(`step-${i}`);
      if (step.classList.contains("done")) continue;
      if (step.classList.contains("active") || !markedError) {
        step.classList.remove("active");
        step.classList.add("error");
        step.querySelector(".step-status").textContent = "failed";
        markedError = true;
      } else {
        step.classList.remove("active", "error");
        step.querySelector(".step-status").textContent = "pending";
      }
    }
  } finally {
    $("generate").disabled = false;
  }
});

// ============================================================
// FILE UPLOAD TAB - NEW FLOW
// ============================================================
$("jdFile").addEventListener("change", e => {
  $("generateFile").disabled = !e.target.files.length;
});

$("generateFile").addEventListener("click", async () => {
  $("status").textContent = "Processing...";
  $("generateFile").disabled = true;
  $("progress").hidden = false;
  resetSteps();

  try {
    const file = $("jdFile").files[0];
    if (!file) throw new Error("No file selected.");

    const settings = await chrome.storage.local.get(["masterTex", "serverUrl"]);
    if (!settings.masterTex) throw new Error("Add your master Overleaf .tex in Settings first.");

    // Step 1: Extract text from file
    markStep(1, "active", "reading...");
    const jdText = await extractTextFromFile(file);
    markStep(1, "done", "extracted");

    if (jdText.length < 30) throw new Error("File contains less than 30 characters.");

    // Step 2: Load master resume
    markStep(2, "active", "loading...");
    await new Promise(r => setTimeout(r, 300));
    markStep(2, "done", "loaded");

    // Step 3: Match keywords
    markStep(3, "active", "matching...");
    await new Promise(r => setTimeout(r, 300));
    markStep(3, "done", "matched");

    // Step 4: Generate tailored LaTeX
    markStep(4, "active", "generating...");
    const base = settings.serverUrl || "http://127.0.0.1:8765";
    const r = await fetch(base + "/generate", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        jd: jdText,
        master_tex: settings.masterTex,
        target_role: $("roleFile").value.trim()
      })
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail?.message || data.detail || "Generation failed.");
    markStep(4, "done", "generated");

    // Step 5: Compile to PDF
    markStep(5, "active", "compiling...");
    await new Promise(r => setTimeout(r, 300));
    markStep(5, "done", "compiled");

    // Step 6: Validation Complete
    markStep(6, "active", "validating...");
    await new Promise(r => setTimeout(r, 300));
    markStep(6, "done", "complete");

    latest = data;
    await chrome.storage.local.set({lastResult: data});
    render(latest);
    $("status").textContent = "Done";
  } catch (e) {
    $("status").textContent = e.message;
    let markedError = false;
    for (let i = 1; i <= 6; i++) {
      const step = $(`step-${i}`);
      if (step.classList.contains("done")) continue;
      if (step.classList.contains("active") || !markedError) {
        step.classList.remove("active");
        step.classList.add("error");
        step.querySelector(".step-status").textContent = "failed";
        markedError = true;
      } else {
        step.classList.remove("active", "error");
        step.querySelector(".step-status").textContent = "pending";
      }
    }
  } finally {
    $("generateFile").disabled = false;
  }
});

async function extractTextFromFile(file) {
  const ext = (file.name.split(".").pop() || "").toLowerCase();
  const type = (file.type || "").toLowerCase();

  if (type === "text/plain" || ext === "txt") {
    return await file.text();
  }

  if (type.includes("word") || ext === "docx") {
    return await extractFromDocx(file);
  }

  if (type === "application/pdf" || ext === "pdf") {
    return await extractViaServer(file);
  }

  throw new Error(`Unsupported file type: ${ext || type}`);
}

async function extractViaServer(file) {
  const settings = await chrome.storage.local.get(["serverUrl"]);
  const base = settings.serverUrl || "http://127.0.0.1:8765";

  const arrayBuffer = await file.arrayBuffer();
  let binary = "";
  const bytes = new Uint8Array(arrayBuffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const content_base64 = btoa(binary);

  const res = await fetch(base + "/extract-text", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      filename: file.name,
      content_base64
    })
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Server failed to extract text from file.");
  }

  const data = await res.json();
  return data.text;
}

async function extractFromDocx(file) {
  // Simple DOCX extraction by parsing XML
  const arrayBuffer = await file.arrayBuffer();
  const zip = new JSZip();
  try {
    await zip.loadAsync(arrayBuffer);
    const docXml = await zip.file("word/document.xml").async("string");
    const text = docXml
      .replace(/<[^>]+>/g, "")  // Remove XML tags
      .replace(/\s+/g, " ")     // Normalize whitespace
      .trim();
    return text;
  } catch (e) {
    throw new Error("Failed to parse DOCX: " + e.message);
  }
}

function render(data) {
  $("result").hidden = false;
  $("pages").textContent = data.page_count ?? "?";
  $("matched").textContent = data.keyword_match?.length ?? 0;
  $("missing").textContent = data.missing_keywords?.length ?? 0;

  // ATS Score with color coding
  const scoreEl = $("atsScore");
  const score = data.ats_score;
  if (score != null) {
    scoreEl.textContent = Math.round(score) + "/100";
    if (score >= 85) {
      scoreEl.style.color = "#22c55e"; // green
    } else if (score >= 70) {
      scoreEl.style.color = "#f59e0b"; // amber
    } else {
      scoreEl.style.color = "#ef4444"; // red
    }
  } else {
    scoreEl.textContent = "-";
    scoreEl.style.color = "";
  }

  $("changes").innerHTML = "";
  for (const x of data.changes || []) {
    const li = document.createElement("li"); li.textContent = x; $("changes").appendChild(li);
  }
  $("notes").innerHTML = "";
  for (const x of data.ats_notes || []) {
    const li = document.createElement("li"); li.textContent = x; $("notes").appendChild(li);
  }
}

$("downloadPdf").addEventListener("click", () => {
  if (!latest?.pdf_base64) return;
  const bytes = Uint8Array.from(atob(latest.pdf_base64), c => c.charCodeAt(0));
  const blob = new Blob([bytes], {type:"application/pdf"});
  const url = URL.createObjectURL(blob);
  chrome.downloads.download({url, filename:"tailored_resume.pdf", saveAs:true});
});

$("downloadTex").addEventListener("click", () => {
  if (!latest?.latex) return;
  const blob = new Blob([latest.latex], {type:"text/plain"});
  const url = URL.createObjectURL(blob);
  chrome.downloads.download({url, filename:"tailored_resume.tex", saveAs:true});
});