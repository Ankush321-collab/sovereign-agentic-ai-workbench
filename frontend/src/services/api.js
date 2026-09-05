
/**
 * services/api.js  —  VAJRA Sovereign AI Workbench Frontend API Client
 * Connects to FastAPI backend at localhost:8000
 */

const BASE = 'http://localhost:8000';

const handle = async (res) => {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
};

// ── Chat / Agent ──────────────────────────────────────────────
export async function sendChat(message, fileId = null) {
  return handle(await fetch(`${BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, file_id: fileId }),
  }));
}

export async function runAgent(query, fileId = null) {
  return handle(await fetch(`${BASE}/api/agent/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, file_id: fileId }),
  }));
}

// ── File upload ───────────────────────────────────────────────
export async function uploadFile(file) {
  const fd = new FormData();
  fd.append('file', file);
  return handle(await fetch(`${BASE}/api/upload`, { method: 'POST', body: fd }));
}

export async function getFiles() {
  return handle(await fetch(`${BASE}/api/files`));
}

export async function downloadFile(filename) {
  const res = await fetch(`${BASE}/api/files/download/${encodeURIComponent(filename)}`);
  if (!res.ok) throw new Error(`Download failed: ${res.status}`);
  const blob = await res.blob();
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click();
  a.remove(); URL.revokeObjectURL(url);
}

// ── Router ────────────────────────────────────────────────────
export async function getModels() {
  return handle(await fetch(`${BASE}/api/router/models`));
}

export async function routeQuery(query, hasImage = false, hasFile = false) {
  return handle(await fetch(`${BASE}/api/router/route`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, has_image: hasImage, has_file: hasFile }),
  }));
}

// ── Network sovereignty ───────────────────────────────────────
export async function getNetworkStatus() {
  return handle(await fetch(`${BASE}/api/network/status`));
}

export async function downloadAuditReport() {
  const res = await fetch(`${BASE}/api/network/audit-export`);
  if (!res.ok) throw new Error('Audit export failed');
  const blob = await res.blob();
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = `VAJRA_AIRGAP_ATTESTATION_${Date.now()}.json`;
  document.body.appendChild(a); a.click();
  a.remove(); URL.revokeObjectURL(url);
}

// ── RAG ───────────────────────────────────────────────────────
export async function ragSearch(query) {
  return handle(await fetch(`${BASE}/api/rag/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  }));
}
