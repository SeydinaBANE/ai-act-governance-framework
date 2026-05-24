import type { ApiError } from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export class ApiRequestError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(detail);
    this.name = "ApiRequestError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const err = (await response.json()) as ApiError;
      detail = err.error ?? detail;
    } catch {
      // keep statusText
    }
    throw new ApiRequestError(response.status, detail);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: (path: string) => request<void>(path, { method: "DELETE" }),

  uploadFile: async <T>(path: string, file: File, extraParams?: Record<string, string>): Promise<T> => {
    const token = getToken();
    const formData = new FormData();
    formData.append("file", file);

    const url = new URL(`${API_BASE}${path}`);
    if (extraParams) {
      Object.entries(extraParams).forEach(([k, v]) => url.searchParams.set(k, v));
    }

    const response = await fetch(url.toString(), {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      let detail = response.statusText;
      try {
        const err = (await response.json()) as ApiError;
        detail = err.error ?? detail;
      } catch {
        // keep statusText
      }
      throw new ApiRequestError(response.status, detail);
    }

    return response.json() as Promise<T>;
  },
};
