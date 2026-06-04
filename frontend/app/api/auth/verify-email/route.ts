import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { CSRF_COOKIE_NAME } from "@/backend/auth/config";
import { describeSupabaseError } from "@/backend/auth/errors";
import { hashToken } from "@/backend/auth/crypto";
import { logSecurityEvent } from "@/backend/auth/logging";
import { attachSessionCookie, issueSessionToken } from "@/backend/auth/session";
import { getSupabaseAdminClient } from "@/backend/auth/supabase";
import { emailVerificationSchema } from "@/backend/auth/validation";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => null);
    const parsed = emailVerificationSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json({ error: "Invalid verification details." }, { status: 400 });
    }

    const { token, csrfToken } = parsed.data;
    const csrfCookie = request.cookies.get(CSRF_COOKIE_NAME)?.value;
    const csrfHeader = request.headers.get("x-csrf-token");

    if (!csrfCookie || csrfCookie !== csrfToken || csrfHeader !== csrfToken) {
      return NextResponse.json({ error: "Invalid verification details." }, { status: 400 });
    }

    const client = getSupabaseAdminClient();
    const tokenHash = hashToken(token);

    const { data: verification, error } = await client
      .from("email_verification_tokens")
      .select("id,user_id,expires_at,used_at")
      .eq("token_hash", tokenHash)
      .maybeSingle();

    if (error) {
      console.error("Verification lookup failed:", describeSupabaseError(error));
      return NextResponse.json({ error: "Authentication service temporarily unavailable." }, { status: 500 });
    }

    if (!verification || verification.used_at || new Date(verification.expires_at).getTime() < Date.now()) {
      return NextResponse.json({ error: "Invalid or expired verification token." }, { status: 400 });
    }

    const updateUser = await client
      .from("users")
      .update({ is_active: true, email_verified_at: new Date().toISOString() })
      .eq("id", verification.user_id);

    if (updateUser.error) {
      console.error("Verification activation failed:", describeSupabaseError(updateUser.error));
      return NextResponse.json({ error: "Authentication service temporarily unavailable." }, { status: 500 });
    }

    const markUsed = await client
      .from("email_verification_tokens")
      .update({ used_at: new Date().toISOString() })
      .eq("id", verification.id);

    if (markUsed.error) {
      console.error("Verification token update failed:", describeSupabaseError(markUsed.error));
      return NextResponse.json({ error: "Authentication service temporarily unavailable." }, { status: 500 });
    }

    const { data: verifiedUser, error: userLookupError } = await client
      .from("users")
      .select("id,email,is_active")
      .eq("id", verification.user_id)
      .maybeSingle();

    if (userLookupError || !verifiedUser || !verifiedUser.is_active) {
      console.error("Verified user lookup failed:", describeSupabaseError(userLookupError));
      return NextResponse.json({ error: "Authentication service temporarily unavailable." }, { status: 500 });
    }

    try {
      await logSecurityEvent(client, "email_verified", {
        userId: verification.user_id,
      });
    } catch (loggingError) {
      console.warn("Unable to log verification event:", loggingError);
    }

    const sessionToken = issueSessionToken({
      id: verifiedUser.id,
      email: verifiedUser.email,
      remember: false,
    });

    const response = NextResponse.json({
      message: "Email verified. You are now signed in.",
    });

    attachSessionCookie(response, sessionToken, false);
    return response;
  } catch (error) {
    console.error("Email verification failed:", describeSupabaseError(error));
    return NextResponse.json({ error: "Authentication service temporarily unavailable." }, { status: 500 });
  }
}
