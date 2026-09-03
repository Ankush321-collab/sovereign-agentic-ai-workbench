/**
 * services/api.js
 * Owner: Roshan (feature/roshan-local-models-frontend)
 *
 * API service layer. Talks to Ankush's FastAPI backend.
 * Falls back to mock data when backend is unavailable.
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'; // default: true

// ── Mock data ────────────────────────────────────────────────────────────────

const MOCK_CHAT_RESPONSE = {
  response:
    'Based on the inspection report and Safety SOP (Page 12), the corrosion on Valve P-101 requires immediate attention per Emergency Procedure EP-04. Recommended action: isolate the valve and schedule replacement within 48 hours.',
  task_type: 'document',
  model: 'qwen2.5:7b-instruct',
  routing_reason: 'Document analysis request detected — using reasoning model.',
  sources: [
    { text: 'EP-04: Emergency valve isolation procedure...', source: 'Safety_SOP.pdf', page: 12, score: 0.94 },
    { text: 'P-101 maintenance schedule and tolerances...', source: 'Maintenance_Manual.pdf', page: 7, score: 0.87 },
  ],
  files: [
    { name: 'Inspection_Approval_Note.docx', type: 'docx', size: '24 KB' },
  ],
  trace: [
    { step: 'Planner',    action: 'Understood user query',          status: 'success' },
    { step: 'Router',     action: 'Selected qwen2.5:7b-instruct',   status: 'success' },
    { step: 'RAG',        action: 'Searched knowledge base (2 hits)',status: 'success' },
    { step: 'Tool',       action: 'Generated DOCX approval note',   status: 'success' },
    { step: 'Reflection', action: 'Verified result quality',         status: 'success' },
    { step: 'Finalizer',  action: 'Response delivered',             status: 'success' },
  ],
};

const MOCK_ROUTING = {
  task_type: 'document',
  model: 'qwen2.5:7b-instruct',
  reason: 'Document summarization request detected.',
  execution: 'LOCAL',
};

const MOCK_NETWORK_STATUS = {
  external_connections: 0,
  local_connections: 4,
  internet_blocked: true,
  models_local: true,
  processing_local: true,
};

const MOCK_FILES = [
  { name: 'Inspection_Approval_Note.docx', type: 'docx', size: '24 KB', created: new Date().toISOString() },
  { name: 'Valve_Calculations.xlsx',       type: 'xlsx', size: '18 KB', created: new Date().toISOString() },
  { name: 'Safety_Report.pptx',            type: 'pptx', size: '56 KB', created: new Date().toISOString() },
];

// ── Helpers ──────────────────────────────────────────────────────────────────

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE_URL}${path}`, opts);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function mockDelay(ms = 600) {
  return new Promise((r) => setTimeout(r, ms));
}

// ── API functions ─────────────────────────────────────────────────────────────

/**
 * POST /chat — Send a chat message (with optional file_id).
 */
export async function sendChat(message, fileId = null) {
  if (USE_MOCK) {
    await mockDelay(1200);
    // Adjust mock routing based on keywords
    const lower = message.toLowerCase();
    let mock = { ...MOCK_CHAT_RESPONSE };
    if (lower.includes('code') || lower.includes('python') || lower.includes('fix')) {
      mock.model = 'qwen2.5-coder:latest';
      mock.task_type = 'coding';
      mock.routing_reason = 'Code/debugging request detected — using coding model.';
    } else if (fileId) {
      mock.model = 'qwen2.5vl:7b';
      mock.task_type = 'vision';
      mock.routing_reason = 'Image attachment detected — using vision model.';
    }
    return mock;
  }
  return request('POST', '/chat', { message, file_id: fileId });
}

/**
 * POST /upload — Upload a file.
 */
export async function uploadFile(file) {
  if (USE_MOCK) {
    await mockDelay(800);
    return { file_id: `mock-${Date.now()}`, filename: file.name, size: file.size };
  }
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE_URL}/upload`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/**
 * GET /routing — Get current routing info.
 */
export async function getRouting() {
  if (USE_MOCK) {
    await mockDelay(300);
    return MOCK_ROUTING;
  }
  return request('GET', '/routing');
}

/**
 * GET /network/status — Get sovereignty/network status.
 */
export async function getNetworkStatus() {
  if (USE_MOCK) {
    await mockDelay(200);
    return MOCK_NETWORK_STATUS;
  }
  return request('GET', '/network/status');
}

/**
 * GET /files — Get list of generated files.
 */
export async function getFiles() {
  if (USE_MOCK) {
    await mockDelay(300);
    return MOCK_FILES;
  }
  const data = await request('GET', '/files');
  if (Array.isArray(data)) return data;
  const deliverables = (data.generated_deliverables || []).map((name) => ({
    name,
    type: name.split('.').pop() || '',
    created: new Date().toISOString(),
  }));
  return deliverables;
}

/**
 * POST /agent/run — Trigger the agent on an uploaded file.
 */
export async function runAgent(fileId, query) {
  if (USE_MOCK) {
    await mockDelay(1000);
    return { ...MOCK_CHAT_RESPONSE, job_id: `mock-job-${Date.now()}` };
  }
  return request('POST', '/agent/run', { file_id: fileId, query });
}

/**
 * GET /agent/status — Poll agent job status.
 */
export async function getAgentStatus(jobId) {
  if (USE_MOCK) {
    await mockDelay(200);
    return { job_id: jobId, status: 'completed', progress: 100 };
  }
  return request('GET', `/agent/status?job_id=${jobId}`);
}
