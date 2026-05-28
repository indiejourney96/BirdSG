import { LOGIN_ATTEMPT_LIMIT, LOGIN_ATTEMPT_WINDOW_MS } from "./config";
import type { SupabaseClient } from "@supabase/supabase-js";

export type LoginAttemptRecord = {
  rate_limit_key: string;
  email: string;
  ip_address: string;
  success: boolean;
  reason: string;
};

export async function isLoginRateLimited(client: SupabaseClient, rateLimitKey: string): Promise<boolean> {
  const cutoffIso = new Date(Date.now() - LOGIN_ATTEMPT_WINDOW_MS).toISOString();
  const { count, error } = await client
    .from("auth_login_attempts")
    .select("id", { count: "exact", head: true })
    .eq("rate_limit_key", rateLimitKey)
    .eq("success", false)
    .gte("attempted_at", cutoffIso);

  if (error) {
    throw error;
  }

  return (count ?? 0) >= LOGIN_ATTEMPT_LIMIT;
}

export async function recordLoginAttempt(client: SupabaseClient, record: LoginAttemptRecord): Promise<void> {
  const { error } = await client.from("auth_login_attempts").insert({
    ...record,
    attempted_at: new Date().toISOString(),
  });

  if (error) {
    throw error;
  }
}
