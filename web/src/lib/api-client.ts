import { cookies } from "next/headers";

const BACKEND = process.env.BACKEND_INTERNAL_URL || "http://backend-api:8000";

interface FetchOptions extends RequestInit {
  authenticated?: boolean;
}

export async function apiFetch(path: string, opts: FetchOptions = {}): Promise<Response> {
  const headers = new Headers(opts.headers);
  headers.set("Content-Type", "application/json");

  if (opts.authenticated !== false) {
    const cookieStore = await cookies();
    const jwt = cookieStore.get("auth_token")?.value;
    if (jwt) {
      headers.set("Authorization", `Bearer ${jwt}`);
    }
  }

  return fetch(`${BACKEND}${path}`, { ...opts, headers, cache: "no-store" });
}

export async function apiJson<T>(path: string, opts: FetchOptions = {}): Promise<T> {
  const r = await apiFetch(path, opts);
  if (!r.ok) {
    const text = await r.text();
    throw new ApiError(r.status, text);
  }
  return (await r.json()) as T;
}

export class ApiError extends Error {
  constructor(public status: number, public body: string) {
    super(`API ${status}: ${body}`);
  }
  json(): unknown {
    try { return JSON.parse(this.body); } catch { return null; }
  }
}
