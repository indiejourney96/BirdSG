import type { NextResponse } from "next/server";
import { AUTH_COOKIE_NAME, isProductionRuntime } from "./config";
import { createSessionToken, verifySessionToken } from "./crypto";

export type SessionUser = {
  id: string;
  email: string;
  remember: boolean;
};

export function issueSessionToken(user: SessionUser): string {
  const ttlSeconds = user.remember ? 60 * 60 * 24 * 30 : 60 * 60 * 24 * 7;
  return createSessionToken({
    sub: user.id,
    email: user.email,
    remember: user.remember,
    ttlSeconds,
  });
}

export function attachSessionCookie(response: NextResponse, token: string, remember: boolean): NextResponse {
  response.cookies.set(AUTH_COOKIE_NAME, token, {
    httpOnly: true,
    secure: isProductionRuntime(),
    sameSite: "lax",
    path: "/",
    maxAge: remember ? 60 * 60 * 24 * 30 : 60 * 60 * 24 * 7,
  });
  return response;
}

export function clearSessionCookie(response: NextResponse): NextResponse {
  response.cookies.set(AUTH_COOKIE_NAME, "", {
    httpOnly: true,
    secure: isProductionRuntime(),
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  return response;
}

export function readVerifiedSessionToken(token: string | undefined) {
  if (!token) {
    return null;
  }

  return verifySessionToken(token);
}

export function shouldUseSecureCookies(): boolean {
  return isProductionRuntime();
}
