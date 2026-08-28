import { supabase } from "./supabase-client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getAuthHeader(): Promise<string | null> {
  return "mock-token";
}

async function handleResponse(response: Response) {
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || `Request failed: ${response.statusText} (${response.status})`);
  }
  return response.json();
}

export const apiClient = {
  async get(endpoint: string) {
    const authHeader = await getAuthHeader();
    const headers: HeadersInit = {};
    if (authHeader) headers["Authorization"] = authHeader;

    const response = await fetch(`${API_BASE_URL}${endpoint}`, { headers });
    return handleResponse(response);
  },

  async post(endpoint: string, body?: any) {
    const authHeader = await getAuthHeader();
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };
    if (authHeader) headers["Authorization"] = authHeader;

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse(response);
  },

  async put(endpoint: string, body: any) {
    const authHeader = await getAuthHeader();
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };
    if (authHeader) headers["Authorization"] = authHeader;

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "PUT",
      headers,
      body: JSON.stringify(body),
    });
    return handleResponse(response);
  },

  async delete(endpoint: string) {
    const authHeader = await getAuthHeader();
    const headers: HeadersInit = {};
    if (authHeader) headers["Authorization"] = authHeader;

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "DELETE",
      headers,
      // Pass content-type for cross-origin verification if needed
      headers: { ...headers }
    });
    return handleResponse(response);
  },

  async uploadFile(endpoint: string, file: File) {
    const authHeader = await getAuthHeader();
    const headers: HeadersInit = {};
    if (authHeader) headers["Authorization"] = authHeader;

    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers,
      body: formData,
    });
    return handleResponse(response);
  },

  getStreamUrl(endpoint: string): string {
    return `${API_BASE_URL}${endpoint}`;
  }
};
