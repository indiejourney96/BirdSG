import crypto from "crypto";
import bcrypt from "bcryptjs";
import { BCRYPT_ROUNDS, getAuthConfig, isProductionRuntime } from "./config";

const JWT_HEADER = { alg: "HS256", typ: "JWT" } as const;

function base64UrlEncode(input: Buffer | string): string {
  const buffer = Buffer.isBuffer(input) ? input : Buffer.from(input);
  return buffer
    .toString("base64")
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replaceAll("=", "");
}

function base64UrlDecode(input: string): Buffer {
  const normalized = input.replaceAll("-", "+").replaceAll("_", "/");
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
  return Buffer.from(padded, "base64");
}

export type SessionTokenPayload = {
  sub: string;
  email: string;
  remember: boolean;
  iat: number;
  exp: number;
};

export function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

export function generateCsrfToken(): string {
  return crypto.randomBytes(32).toString("base64url");
}

export function getCsrfCookieOptions() {
  return {
    httpOnly: false,
    secure: isProductionRuntime(),
    sameSite: "strict" as const,
    path: "/",
  };
}

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, BCRYPT_ROUNDS);
}

export async function verifyPassword(password: string, passwordHash: string): Promise<boolean> {
  return bcrypt.compare(password, passwordHash);
}

export function hashToken(token: string): string {
  return crypto.createHash("sha256").update(token).digest("hex");
}

export function generatePasswordResetToken(): string {
  return crypto.randomBytes(32).toString("base64url");
}

export function createSessionToken(payload: Omit<SessionTokenPayload, "iat" | "exp"> & { ttlSeconds: number }): string {
  const config = getAuthConfig();
  const issuedAt = Math.floor(Date.now() / 1000);
  const tokenPayload: SessionTokenPayload = {
    sub: payload.sub,
    email: payload.email,
    remember: payload.remember,
    iat: issuedAt,
    exp: issuedAt + payload.ttlSeconds,
  };

  const header = base64UrlEncode(JSON.stringify(JWT_HEADER));
  const body = base64UrlEncode(JSON.stringify(tokenPayload));
  const message = `${header}.${body}`;
  const signature = crypto.createHmac("sha256", config.sessionSecret).update(message).digest();

  return `${message}.${base64UrlEncode(signature)}`;
}

export function verifySessionToken(token: string): SessionTokenPayload | null {
  try {
    const config = getAuthConfig();
    const [headerSegment, payloadSegment, signatureSegment] = token.split(".");

    if (!headerSegment || !payloadSegment || !signatureSegment) {
      return null;
    }

    const expectedSignature = crypto
      .createHmac("sha256", config.sessionSecret)
      .update(`${headerSegment}.${payloadSegment}`)
      .digest();
    const providedSignature = base64UrlDecode(signatureSegment);

    if (
      expectedSignature.length !== providedSignature.length ||
      !crypto.timingSafeEqual(expectedSignature, providedSignature)
    ) {
      return null;
    }

    const payload = JSON.parse(base64UrlDecode(payloadSegment).toString("utf8")) as SessionTokenPayload;

    if (!payload?.sub || !payload?.email || !payload?.exp || payload.exp <= Math.floor(Date.now() / 1000)) {
      return null;
    }

    return payload;
  } catch {
    return null;
  }
}

export function getSessionCookieOptions(remember: boolean) {
  return {
    httpOnly: true,
    secure: isProductionRuntime(),
    sameSite: "lax" as const,
    path: "/",
    maxAge: remember ? 60 * 60 * 24 * 30 : 60 * 60 * 24 * 7,
  };
}

export function clearSessionCookieOptions() {
  return {
    httpOnly: true,
    secure: isProductionRuntime(),
    sameSite: "lax" as const,
    path: "/",
    maxAge: 0,
  };
}

export function getRequestIp(headers: Headers): string {
  const forwardedFor = headers.get("x-forwarded-for");
  const realIp = headers.get("x-real-ip");
  const ip = forwardedFor?.split(",")[0]?.trim() || realIp?.trim() || "0.0.0.0";
  return ip;
}
