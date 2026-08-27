import { supabase } from "./supabase-client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getAuthHeader(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession();
  return session ? `Bearer ${session.access_token}` : null;
}

export const apiClient = {
  async get(endpoint: string) {
    const authHeader = await getAuthHeader();
    const headers: HeadersInit = {};
    if (authHeader) headers["Authorization"] = authHeader;

    const response = await fetch(`${API_BASE_URL}${endpoint}`, { headers });
    if (!response.ok) {
      throw new Error(`GET request failed: ${response.statusText} (${response.status})`);
    }
    return response.json();
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
    if (!response.ok) {
      throw new Error(`POST request failed: ${response.statusText} (${response.status})`);
    }
    return response.json();
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
    if (!response.ok) {
      throw new Error(`PUT request failed: ${response.statusText} (${response.status})`);
    }
    return response.json();
  },

  async delete(endpoint: string) {
    const authHeader = await getAuthHeader();
    const headers: HeadersInit = {};
    if (authHeader) headers["Authorization"] = authHeader;

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "DELETE",
      headers,
    });
    if (!response.ok) {
      throw new Error(`DELETE request failed: ${response.statusText} (${response.status})`);
    }
    return response.json();
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
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Upload request failed: ${response.statusText}`);
    }
    return response.json();
  },

  getStreamUrl(endpoint: string): string {
    return `${API_BASE_URL}${endpoint}`;
  }
};
