import { NextRequest, NextResponse } from "next/server";
import { CSRF_COOKIE_NAME } from "@/backend/auth/config";
import { hashPassword, hashToken } from "@/backend/auth/crypto";
import { logSecurityEvent } from "@/backend/auth/logging";
import { getSupabaseAdminClient } from "@/backend/auth/supabase";
import { passwordResetConfirmSchema } from "@/backend/auth/validation";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => null);
    const parsed = passwordResetConfirmSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json({ error: "Invalid reset details." }, { status: 400 });
    }

    const { token, password } = parsed.data;
    const csrfCookie = request.cookies.get(CSRF_COOKIE_NAME)?.value;
    const csrfHeader = request.headers.get("x-csrf-token");

    if (!csrfCookie || csrfCookie !== csrfHeader) {
      return NextResponse.json({ error: "Invalid reset details." }, { status: 400 });
    }

    const client = getSupabaseAdminClient();
    const tokenHash = hashToken(token);

    const { data: resetToken, error } = await client
      .from("password_reset_tokens")
      .select("id,user_id,expires_at,used_at")
      .eq("token_hash", tokenHash)
      .maybeSingle();

    if (error) {
      throw error;
    }

    const tokenExpired = !resetToken || new Date(resetToken.expires_at).getTime() < Date.now() || resetToken.used_at;

    if (tokenExpired) {
      try {
        await logSecurityEvent(client, "password_reset_failed", {
          reason: "expired_or_invalid_token",
        });
      } catch (loggingError) {
        console.warn("Unable to log password reset failure:", loggingError);
      }

      return NextResponse.json({ error: "Invalid or expired reset token." }, { status: 400 });
    }

    const passwordHash = await hashPassword(password);

    await client.from("users").update({ password_hash: passwordHash }).eq("id", resetToken.user_id);
    await client
      .from("password_reset_tokens")
      .update({ used_at: new Date().toISOString() })
      .eq("id", resetToken.id);

    try {
      await logSecurityEvent(client, "password_reset_completed", {
        userId: resetToken.user_id,
      });
    } catch (loggingError) {
      console.warn("Unable to log password reset success:", loggingError);
    }

    return NextResponse.json({ message: "Password updated successfully." });
  } catch (error) {
    console.error("Password reset confirmation failed:", error);
    return NextResponse.json({ error: "Something went wrong." }, { status: 500 });
  }
}
