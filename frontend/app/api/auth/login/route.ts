import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { CSRF_COOKIE_NAME } from "@/backend/auth/config";
import { getRequestIp, normalizeEmail, verifyPassword } from "@/backend/auth/crypto";
import { logSecurityEvent } from "@/backend/auth/logging";
import { isLoginRateLimited, recordLoginAttempt } from "@/backend/auth/rate-limit";
import { attachSessionCookie, issueSessionToken } from "@/backend/auth/session";
import { getSupabaseAdminClient } from "@/backend/auth/supabase";
import { loginSchema } from "@/backend/auth/validation";

export const runtime = "nodejs";

const DUMMY_PASSWORD_HASH = bcrypt.hashSync("not-the-password", 12);

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => null);
    const parsed = loginSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json({ error: "Invalid credentials." }, { status: 400 });
    }

    const { email, password, rememberMe, csrfToken } = parsed.data;
    const csrfCookie = request.cookies.get(CSRF_COOKIE_NAME)?.value;
    const csrfHeader = request.headers.get("x-csrf-token");

    if (!csrfCookie || csrfCookie !== csrfToken || csrfHeader !== csrfToken) {
      return NextResponse.json({ error: "Invalid credentials." }, { status: 400 });
    }

    const client = getSupabaseAdminClient();
    const ipAddress = getRequestIp(request.headers);
    const rateLimitKey = `${normalizeEmail(email)}|${ipAddress}`;

    if (await isLoginRateLimited(client, rateLimitKey)) {
      await logSecurityEvent(client, "login_rate_limited", {
        email: normalizeEmail(email),
        ipAddress,
      });

      return NextResponse.json(
        { error: "Too many login attempts. Please try again later." },
        { status: 429 },
      );
    }

    const { data: user, error } = await client
      .from("users")
      .select("id,email,password_hash,is_active")
      .eq("email", email)
      .maybeSingle();

    if (error) {
      throw error;
    }

    const passwordHash = user?.password_hash ?? DUMMY_PASSWORD_HASH;
    const passwordMatches = await verifyPassword(password, passwordHash);
    const currentUser = user;
    const validUser = Boolean(currentUser && currentUser.is_active && passwordMatches);

    try {
      await recordLoginAttempt(client, {
        rate_limit_key: rateLimitKey,
        email,
        ip_address: ipAddress,
        success: validUser,
        reason: validUser ? "login_success" : "invalid_credentials",
      });
    } catch (loggingError) {
      console.warn("Unable to record login attempt:", loggingError);
    }

    try {
      await logSecurityEvent(client, validUser ? "login_success" : "login_failure", {
        email,
        ipAddress,
        outcome: validUser ? "success" : "failure",
      });
    } catch (loggingError) {
      console.warn("Unable to log security event:", loggingError);
    }

    if (!currentUser || !currentUser.is_active || !passwordMatches) {
      return NextResponse.json({ error: "Invalid credentials." }, { status: 401 });
    }

    const sessionToken = issueSessionToken({
      id: currentUser.id,
      email: currentUser.email,
      remember: rememberMe,
    });

    try {
      await client.from("users").update({ last_login: new Date().toISOString() }).eq("id", currentUser.id);
    } catch (updateError) {
      console.warn("Unable to update last_login:", updateError);
    }

    const response = NextResponse.json({
      user: {
        id: currentUser.id,
        email: currentUser.email,
      },
    });

    attachSessionCookie(response, sessionToken, rememberMe);

    return response;
  } catch (error) {
    console.error("Login failed:", error);
    return NextResponse.json({ error: "Something went wrong." }, { status: 500 });
  }
}
