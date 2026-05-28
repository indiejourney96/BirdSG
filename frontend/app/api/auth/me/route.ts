import { NextRequest, NextResponse } from "next/server";
import { getSupabaseAdminClient } from "@/backend/auth/supabase";
import { readVerifiedSessionToken } from "@/backend/auth/session";
import { AUTH_COOKIE_NAME } from "@/backend/auth/config";

export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  const session = readVerifiedSessionToken(token);

  if (!session) {
    return NextResponse.json({ authenticated: false }, { status: 401 });
  }

  const client = getSupabaseAdminClient();
  const { data: user, error } = await client
    .from("users")
    .select("id,email,last_login,is_active,created_at,email_verified_at")
    .eq("id", session.sub)
    .maybeSingle();

  if (error || !user || !user.is_active) {
    return NextResponse.json({ authenticated: false }, { status: 401 });
  }

  return NextResponse.json({
    authenticated: true,
    user: {
      id: user.id,
      email: user.email,
      lastLogin: user.last_login,
      createdAt: user.created_at,
      emailVerifiedAt: user.email_verified_at,
    },
  });
}
