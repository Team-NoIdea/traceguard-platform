/**
 * Thin fetch wrapper around the TraceGuard backend.
 *
 * Phase 1: feature `api.ts` modules (see src/features/*\/api.ts) do NOT
 * call this yet â€” they resolve mock data instead, so there is nothing
 * real to point at. This client exists so Phase 2 has a single,
 * already-typed transport to swap the mock resolvers for, without
 * touching hooks, pages, or components.
 */

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function authHeaders(): Promise<Record<string, string>> {
  const { firebaseAuth } = await import("./firebase");
  const token = firebaseAuth?.currentUser
    ? await firebaseAuth.currentUser.getIdToken()
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
  const authorization = await authHeaders();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...authorization },
    ...init,
  });

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
