/** Authenticated API transport with one token-refresh retry. */

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function authHeaders(forceRefresh = false): Promise<Record<string, string>> {
  const { firebaseAuth } = await import("./firebase");
  const token = firebaseAuth?.currentUser
    ? await firebaseAuth.currentUser.getIdToken(forceRefresh)
    : undefined;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<TResponse>(
  path: string,
  init?: RequestInit,
): Promise<TResponse> {
  const send = async (forceRefresh = false) => {
    const headers = new Headers(init?.headers);
    headers.set("Content-Type", "application/json");
    const authorization = await authHeaders(forceRefresh);
    if (authorization.Authorization) headers.set("Authorization", authorization.Authorization);
    return fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  };
  let response = await send();
  if (response.status === 401) {
    const { firebaseAuth } = await import("./firebase");
    if (firebaseAuth?.currentUser) response = await send(true);
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, typeof body?.detail === "string" ? body.detail : `Request failed (${response.status})`);
  }

  return (await response.json()) as TResponse;
}

export const apiClient = {
  get: <TResponse>(path: string) => request<TResponse>(path),
  post: <TResponse, TBody = unknown>(path: string, body?: TBody) =>
    request<TResponse>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),
};
