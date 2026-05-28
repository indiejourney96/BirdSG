import { NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE_NAME } from "@/backend/auth/config";

const PUBLIC_PATHS = new Set(["/login", "/forgot-password", "/reset-password"]);

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const sessionCookie = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  const isApiAuthRoute = pathname.startsWith("/api/auth");
  const isPublicAsset =
    pathname.startsWith("/_next") || pathname === "/favicon.ico" || pathname.startsWith("/assets");

  if (isApiAuthRoute || isPublicAsset) {
    return NextResponse.next();
  }

  if (!sessionCookie && !PUBLIC_PATHS.has(pathname)) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  if (sessionCookie && PUBLIC_PATHS.has(pathname)) {
    const homeUrl = new URL("/", request.url);
    return NextResponse.redirect(homeUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
