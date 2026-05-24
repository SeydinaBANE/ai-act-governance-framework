"use client";

import type { TokenResponse, User } from "@/types/api";

const TOKEN_KEY = "access_token";

export function saveToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  const token = getToken();
  if (!token) return false;

  try {
    const [, payload] = token.split(".");
    const decoded = JSON.parse(atob(payload));
    return decoded.exp * 1000 > Date.now();
  } catch {
    return false;
  }
}

export function getUserFromToken(): Partial<User> | null {
  const token = getToken();
  if (!token) return null;

  try {
    const [, payload] = token.split(".");
    return JSON.parse(atob(payload)) as Partial<User>;
  } catch {
    return null;
  }
}
