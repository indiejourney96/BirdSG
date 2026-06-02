import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { CSRF_COOKIE_NAME, EMAIL_VERIFICATION_TOKEN_TTL_MS } from "@/backend/auth/config";
import { describeSupabaseError } from "@/backend/auth/errors";
import {
  generateCsrfToken,
  generatePasswordResetToken,
  getCsrfCookieOptions,
  getRequestIp,
  hashPassword,
  hashToken,
  normalizeEmail,
} from "@/backend/auth/crypto";
import { logSecurityEvent } from "@/backend/auth/logging";
import { getSupabaseAdminClient } from "@/backend/auth/supabase";
import { signupSchema } from "@/backend/auth/validation";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => null);
    const parsed = signupSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json({ error: "Invalid signup details." }, { status: 400 });
    }

    const { email, password, csrfToken } = parsed.data;
    const csrfCookie = request.cookies.get(CSRF_COOKIE_NAME)?.value;
    const csrfHeader = request.headers.get("x-csrf-token");

    if (!csrfCookie || csrfCookie !== csrfToken || csrfHeader !== csrfToken) {
      return NextResponse.json({ error: "Invalid signup details." }, { status: 400 });
    }

    const client = getSupabaseAdminClient();
    const normalizedEmail = normalizeEmail(email);
    const existing = await client.from("users").select("id").eq("email", normalizedEmail).maybeSingle();

    if (existing.error) {
      console.error("Signup lookup failed:", describeSupabaseError(existing.error));
      return NextResponse.json({ error: "Authentication service temporarily unavailable." }, { status: 500 });
    }

    if (existing.data) {
      return NextResponse.json({ error: "An account with this email already exists." }, { status: 409 });
    }

    const passwordHash = await hashPassword(password);
    const createdAt = new Date().toISOString();
    const userInsert = await client
      .from("users")
      .insert({
        email: normalizedEmail,
        password_hash: passwordHash,
        is_active: false,
        email_verified_at: null,
        created_at: createdAt,
      })
      .select("id")
      .single();

    if (userInsert.error || !userInsert.data) {
      console.error("Signup insert failed:", describeSupabaseError(userInsert.error));
      return NextResponse.json({ error: "Authentication service temporarily unavailable." }, { status: 500 });
    }

    const verificationToken = generatePasswordResetToken();
    const verificationHash = hashToken(verificationToken);
    const expiresAt = new Date(Date.now() + EMAIL_VERIFICATION_TOKEN_TTL_MS).toISOString();

    const tokenInsert = await client.from("email_verification_tokens").insert({
      user_id: userInsert.data.id,
      token_hash: verificationHash,
      expires_at: expiresAt,
    });

    if (tokenInsert.error) {
      console.error("Verification token insert failed:", describeSupabaseError(tokenInsert.error));
      return NextResponse.json({ error: "Authentication service temporarily unavailable." }, { status: 500 });
    }

    try {
      await logSecurityEvent(client, "signup_created", {
        email: normalizedEmail,
        ipAddress: getRequestIp(request.headers),
      });
    } catch (loggingError) {
      console.warn("Unable to log signup event:", loggingError);
    }

    const responseBody: Record<string, unknown> = {
      message: "Account created. Check your email to verify your account.",
    };

    if (process.env.NODE_ENV !== "production") {
      responseBody.verificationUrl = `${process.env.NEXT_PUBLIC_APP_BASE_URL ?? "http://localhost:3000"}/verify-email?token=${verificationToken}`;
    }

    const response = NextResponse.json(responseBody, { status: 201 });
    response.cookies.set(CSRF_COOKIE_NAME, generateCsrfToken(), getCsrfCookieOptions());
    return response;
  } catch (error) {
    console.error("Signup failed:", describeSupabaseError(error));
    return NextResponse.json({ error: "Authentication service temporarily unavailable." }, { status: 500 });
  }
}
