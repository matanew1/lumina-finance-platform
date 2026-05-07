const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function requestJson(path, options = {}) {
  // TODO: add typed request/response handling, errors, and auth headers.
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const data = await response.json().catch(() => null);

  return {
    ok: response.ok,
    status: response.status,
    data
  };
}

export async function uploadTransactions(file) {
  // TODO: build FormData and call POST /upload-transactions.
  return { ok: false, status: 501, data: { status: "todo", fileName: file?.name } };
}
