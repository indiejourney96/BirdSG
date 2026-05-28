import { NextResponse } from "next/server";
import { AUTH_COOKIE_NAME } from "@/backend/auth/config";
import { clearSessionCookie } from "@/backend/auth/session";
import { logSecurityEvent } from "@/backend/auth/logging";
import { getSupabaseAdminClient } from "@/backend/auth/supabase";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const client = getSupabaseAdminClient();
  const response = NextResponse.json({ ok: true });

  clearSessionCookie(response);

  try {
    await logSecurityEvent(client, "logout", {
      hasCookie: request.headers.get("cookie")?.includes(AUTH_COOKIE_NAME) ?? false,
    });
  } catch (error) {
    console.error("Logout event logging failed:", error);
  }

  return response;
}
