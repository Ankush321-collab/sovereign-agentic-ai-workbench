
/**
 * services/api.js  —  VAJRA Sovereign AI Workbench Frontend API Client
 * Connects to FastAPI backend at localhost:8000
 */

const BASE = import.meta.env.VITE_API_URL || '';

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

/**
 * Real-Time SSE Agent Streaming Client
 * Parses SSE events ('plan', 'router', 'rag', 'tool_start', 'tool_output', 'token', 'deliverables', 'done')
 */
export async function streamAgent(query, fileId = null, onEvent = () => {}, onError = () => {}, onDone = () => {}) {
  try {
    const response = await fetch(`${BASE}/api/agent/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, file_id: fileId }),
    });

    if (!response.ok) {
      const errTxt = await response.text();
      throw new Error(errTxt || `HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // Keep unfinished line in buffer

      let currentEvent = 'message';
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.replace('event: ', '').trim();
        } else if (line.startsWith('data: ')) {
          const rawData = line.replace('data: ', '').trim();
          if (rawData) {
            try {
              const parsed = JSON.parse(rawData);
              onEvent({ event: currentEvent, data: parsed });
              if (currentEvent === 'done') {
                onDone(parsed);
              }
            } catch (jsonErr) {
              console.warn('Failed to parse SSE data:', rawData, jsonErr);
            }
          }
        }
      }
    }
  } catch (err) {
    console.error('SSE Stream error:', err);
    onError(err);
  }
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

export function getDownloadUrl(filename) {
  return `${BASE}/api/files/download/${encodeURIComponent(filename)}`;
}

export async function downloadFile(filename) {
  const url = getDownloadUrl(filename);
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      a.remove();
      URL.revokeObjectURL(blobUrl);
    }, 1500);
  } catch (err) {
    console.warn('Blob download fallback:', err);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => a.remove(), 1000);
  }
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
