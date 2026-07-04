import type { SupabaseClient } from "@supabase/supabase-js";

export async function logSecurityEvent(
  client: SupabaseClient,
  eventType: string,
  details: Record<string, unknown>,
): Promise<void> {
  const { error } = await client.from("auth_security_events").insert({
    event_type: eventType,
    details,
    created_at: new Date().toISOString(),
  });

  if (error) {
    throw error;
  }
}
