"use client";

import { useMemo } from "react";
import axios, { AxiosInstance } from "axios";
import { useAuth } from "@clerk/nextjs";

/** Backend base URL as reachable from the browser (no trailing slash). */
export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");

/** WebSocket base URL derived from API_URL (http -> ws, https -> wss). */
export const WS_URL = API_URL.replace(/^http/, "ws");

/**
 * Axios instance for the SynthTeam backend that attaches the signed-in
 * user's Clerk session token to every request.
 */
export function useApi(): AxiosInstance {
  const { getToken } = useAuth();

  return useMemo(() => {
    const instance = axios.create({ baseURL: API_URL });
    instance.interceptors.request.use(async (config) => {
      const token = await getToken();
      if (token) config.headers.set("Authorization", `Bearer ${token}`);
      return config;
    });
    return instance;
  }, [getToken]);
}

/** Best-effort error message from an axios error. */
export function apiErrorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (detail) return JSON.stringify(detail);
    if (err.message) return err.message;
  }
  return fallback;
}
