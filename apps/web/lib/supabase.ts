/**
 * Browser-safe Supabase client for LedgerOS Command Center.
 * Exposes only safe public client configurations (NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY).
 * Never exposes SECRET_KEY, DATABASE_URL, or passwords to the browser.
 */

import { createClient, SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://gfcteazsljcsikyuqjji.supabase.co";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "sb_publishable_ZgJnkHVrNBi_e2ii59u_Sw_6xcgh99A";

let supabaseClient: SupabaseClient | null = null;

export function getSupabaseClient(): SupabaseClient {
  if (!supabaseClient) {
    supabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
      },
    });
  }
  return supabaseClient;
}

/**
 * Returns Authorization header with Supabase access token if session is active.
 * Used for authenticating API requests (e.g. POST /api/approvals/{id}/action).
 */
export async function getAuthHeaders(): Promise<Record<string, string>> {
  try {
    const client = getSupabaseClient();
    const { data } = await client.auth.getSession();
    const token = data?.session?.access_token;
    if (token) {
      return {
        Authorization: `Bearer ${token}`,
      };
    }
  } catch (err) {
    console.warn("Failed to retrieve Supabase session token:", err);
  }
  return {};
}
