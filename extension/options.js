async function load() {
  const x = await chrome.storage.local.get(['masterTex', 'serverUrl']);
  document.getElementById('masterTex').value = x.masterTex || '';
  document.getElementById('serverUrl').value = x.serverUrl || 'http://localhost:8000';
}
load();

document.getElementById('save').onclick = async () => {
  await chrome.storage.local.set({
    masterTex: document.getElementById('masterTex').value,
    serverUrl: document.getElementById('serverUrl').value.replace(/\/$/, '')
  });
  document.getElementById('msg').textContent = ' Saved.';
  setTimeout(() => { document.getElementById('msg').textContent = ''; }, 3000);
};

document.getElementById('syncServerMaster').onclick = async () => {
  const url = document.getElementById('serverUrl').value.replace(/\/$/, '');
  const statusEl = document.getElementById('serverStatus');
  statusEl.textContent = 'Fetching master resume from server...';
  try {
    const res = await fetch(url + '/master-resume');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    if (data.latex) {
      document.getElementById('masterTex').value = data.latex;
      await chrome.storage.local.set({ masterTex: data.latex });
      statusEl.innerHTML = '<span style=\"color:green;font-weight:bold;\">Successfully loaded Master Resume from server and saved!</span>';
    }
  } catch (e) {
    statusEl.innerHTML = '<span style=\"color:red;font-weight:bold;\">Failed to fetch:</span> ' + e.message;
  }
};

document.getElementById('testConn').onclick = async () => {
  const url = document.getElementById('serverUrl').value.replace(/\/$/, '');
  const statusEl = document.getElementById('serverStatus');
  statusEl.textContent = 'Connecting to server...';
  try {
    const res = await fetch(url + '/health');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    statusEl.innerHTML = 
      '<span style=\"color:green;font-weight:bold;\">Server Connected!</span><br>' +
      'pdflatex: <b>' + (data.pdflatex ? 'Available' : 'Not Found') + '</b> | ' +
      'pdfinfo: <b>' + (data.pdfinfo ? 'Available' : 'Not Found') + '</b> | ' +
      'pdftotext: <b>' + (data.pdftotext ? 'Available' : 'Not Found') + '</b>';
  } catch (e) {
    statusEl.innerHTML = '<span style=\"color:red;font-weight:bold;\">Connection Failed:</span> ' + e.message + '. Make sure server is running at ' + url + '.';
  }
};


