import { NextResponse } from "next/server";
import { CSRF_COOKIE_NAME } from "@/backend/auth/config";
import { generateCsrfToken, getCsrfCookieOptions } from "@/backend/auth/crypto";

export const runtime = "nodejs";

export async function GET() {
  const csrfToken = generateCsrfToken();
  const response = NextResponse.json({ csrfToken });

  response.cookies.set(CSRF_COOKIE_NAME, csrfToken, getCsrfCookieOptions());

  return response;
}
