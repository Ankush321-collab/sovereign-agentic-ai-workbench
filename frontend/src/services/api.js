/**
 * services/api.js
 * Sovereign AI Workbench - Frontend API Client
 */

const BASE_URL = 'http://localhost:8000';

export async function getNetworkStatus() {
  const res = await fetch(`${BASE_URL}/api/network/status`);
  if (!res.ok) throw new Error('Failed to fetch network status');
  return res.json();
}

export async function downloadAuditReport() {
  const res = await fetch(`${BASE_URL}/api/network/audit-export`);
  if (!res.ok) throw new Error('Failed to export audit report');
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `AIRGAP_SECURITY_ATTESTATION_${Date.now()}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function getRouting() {
  const res = await fetch(`${BASE_URL}/api/router/models`);
  if (!res.ok) throw new Error('Failed to fetch models');
  return res.json();
}

export async function routeQuery(query, hasImage = false, hasFile = false) {
  const res = await fetch(`${BASE_URL}/api/router/route`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, has_image: hasImage, has_file: hasFile })
  });
  if (!res.ok) throw new Error('Failed to route query');
  return res.json();
}

export async function runAgentWorkflow(query, ocrReadings = null) {
  const res = await fetch(`${BASE_URL}/api/agent/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, ocr_readings: ocrReadings })
  });
  if (!res.ok) throw new Error('Agent execution failed');
  return res.json();
}
