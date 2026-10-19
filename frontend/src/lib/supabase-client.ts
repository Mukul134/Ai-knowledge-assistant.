import { createBrowserClient } from "@supabase/ssr";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error("Supabase client configuration is unavailable. Check SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY.");
}

// Singleton browser client for Supabase operations on the client-side
export const supabase = createBrowserClient(supabaseUrl, supabaseAnonKey);
