async function load() {
  const x = await chrome.storage.local.get(["masterTex", "serverUrl"]);
  document.getElementById("masterTex").value = x.masterTex || "";
  document.getElementById("serverUrl").value = x.serverUrl || "http://127.0.0.1:8765";
}
load();

document.getElementById("save").onclick = async () => {
  await chrome.storage.local.set({
    masterTex: document.getElementById("masterTex").value,
    serverUrl: document.getElementById("serverUrl").value.replace(/\/$/, "")
  });
  document.getElementById("msg").textContent = " Saved.";
  setTimeout(() => { document.getElementById("msg").textContent = ""; }, 3000);
};

document.getElementById("syncServerMaster").onclick = async () => {
  const url = document.getElementById("serverUrl").value.replace(/\/$/, "");
  const statusEl = document.getElementById("serverStatus");
  statusEl.textContent = "Fetching master resume from server...";
  try {
    const res = await fetch(url + "/master-resume");
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    if (data.latex) {
      document.getElementById("masterTex").value = data.latex;
      await chrome.storage.local.set({ masterTex: data.latex });
      statusEl.innerHTML = `<span style="color:green;font-weight:bold;">Successfully loaded Master Resume with 9 Projects from server and saved!</span>`;
    }
  } catch (e) {
    statusEl.innerHTML = `<span style="color:red;font-weight:bold;">Failed to fetch:</span> ${e.message}`;
  }
};

document.getElementById("testConn").onclick = async () => {
  const url = document.getElementById("serverUrl").value.replace(/\/$/, "");
  const statusEl = document.getElementById("serverStatus");
  statusEl.textContent = "Connecting to server...";
  try {
    const res = await fetch(url + "/health");
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    statusEl.innerHTML = `
      <span style="color:green;font-weight:bold;">Server Connected!</span><br>
      Model: <code>${data.gemini_model || "N/A"}</code> | 
      pdflatex: <b>${data.pdflatex ? "Available" : "Not Found"}</b> | 
      Gemini API Key: <b>${data.gemini_key_configured ? "Configured" : "Not set (set in server/.env)"}</b>
    `;
  } catch (e) {
    statusEl.innerHTML = `<span style="color:red;font-weight:bold;">Connection Failed:</span> ${e.message}. Make sure server is running at ${url}.`;
  }
};
