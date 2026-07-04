import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { getAuthConfig } from "./config";

let adminClient: SupabaseClient | null = null;

export function getSupabaseAdminClient(): SupabaseClient {
  if (!adminClient) {
    const { supabaseUrl, supabaseServiceRoleKey } = getAuthConfig();
    adminClient = createClient(supabaseUrl, supabaseServiceRoleKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      },
    });
  }

  return adminClient;
}
