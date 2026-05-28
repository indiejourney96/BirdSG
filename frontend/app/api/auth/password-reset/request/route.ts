import { NextRequest, NextResponse } from "next/server";
import { CSRF_COOKIE_NAME, PASSWORD_RESET_TOKEN_TTL_MS } from "@/backend/auth/config";
import { generatePasswordResetToken, hashToken } from "@/backend/auth/crypto";
import { logSecurityEvent } from "@/backend/auth/logging";
import { getSupabaseAdminClient } from "@/backend/auth/supabase";
import { passwordResetRequestSchema } from "@/backend/auth/validation";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => null);
    const parsed = passwordResetRequestSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json({ error: "Invalid request." }, { status: 400 });
    }

    const { email } = parsed.data;
    const csrfCookie = request.cookies.get(CSRF_COOKIE_NAME)?.value;
    const csrfHeader = request.headers.get("x-csrf-token");

    if (!csrfCookie || csrfCookie !== csrfHeader) {
      return NextResponse.json({ error: "Invalid request." }, { status: 400 });
    }

    const client = getSupabaseAdminClient();
    const { data: user } = await client.from("users").select("id,is_active").eq("email", email).maybeSingle();

    if (user?.is_active) {
      const resetToken = generatePasswordResetToken();
      const tokenHash = hashToken(resetToken);
      const expiresAt = new Date(Date.now() + PASSWORD_RESET_TOKEN_TTL_MS).toISOString();

      await client.from("password_reset_tokens").insert({
        user_id: user.id,
        token_hash: tokenHash,
        expires_at: expiresAt,
      });

      try {
        await logSecurityEvent(client, "password_reset_requested", {
          email,
          expiresAt,
        });
      } catch (loggingError) {
        console.warn("Unable to log password reset request:", loggingError);
      }

      if (process.env.NODE_ENV !== "production") {
        const resetUrl = `${process.env.NEXT_PUBLIC_APP_BASE_URL ?? "http://localhost:3000"}/reset-password?token=${resetToken}`;
        return NextResponse.json({
          message: "If an account exists, a reset link has been generated.",
          resetUrl,
        });
      }
    }

    return NextResponse.json({
      message: "If an account exists, a reset link has been generated.",
    });
  } catch (error) {
    console.error("Password reset request failed:", error);
    return NextResponse.json({ error: "Something went wrong." }, { status: 500 });
  }
}
