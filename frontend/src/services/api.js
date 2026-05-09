const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const message = data?.detail ?? `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return data;
}

export function fetchClients() {
  return requestJson("/clients");
}

export function fetchClientPositions(clientId) {
  return requestJson(`/clients/${encodeURIComponent(clientId)}/positions`);
}

export function fetchViolations(clientId) {
  const query = clientId ? `?client_id=${encodeURIComponent(clientId)}` : "";
  return requestJson(`/violations${query}`);
}

export function fetchAnalytics() {
  return requestJson("/analytics");
}

export function uploadTransactions(file) {
  const formData = new FormData();
  formData.append("file", file);

  return requestJson("/upload-transactions", {
    method: "POST",
    body: formData
  });
}
