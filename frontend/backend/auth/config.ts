export const AUTH_COOKIE_NAME = "birdsg_session";
export const CSRF_COOKIE_NAME = "birdsg_csrf";
export const LOGIN_ATTEMPT_WINDOW_MS = 15 * 60 * 1000;
export const LOGIN_ATTEMPT_LIMIT = 5;
export const PASSWORD_RESET_TOKEN_TTL_MS = 30 * 60 * 1000;
export const BCRYPT_ROUNDS = 12;
export const SESSION_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;
export const REMEMBER_ME_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 30;

export type AuthRuntimeConfig = {
  supabaseUrl: string;
  supabaseServiceRoleKey: string;
  sessionSecret: string;
  appBaseUrl: string;
  nodeEnv: "development" | "production" | "test";
};

function requireEnv(name: string): string {
  const value = process.env[name];

  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }

  return value.trim();
}

export function getAuthConfig(): AuthRuntimeConfig {
  const nodeEnv = (process.env.NODE_ENV ?? "development") as AuthRuntimeConfig["nodeEnv"];
  const appBaseUrl =
    process.env.NEXT_PUBLIC_APP_BASE_URL?.trim() ??
    process.env.APP_BASE_URL?.trim() ??
    "http://localhost:3000";

  return {
    supabaseUrl: requireEnv("SUPABASE_URL"),
    supabaseServiceRoleKey: requireEnv("SUPABASE_SERVICE_ROLE_KEY"),
    sessionSecret: requireEnv("AUTH_SESSION_SECRET"),
    appBaseUrl,
    nodeEnv,
  };
}

export function isProductionRuntime(): boolean {
  return getAuthConfig().nodeEnv === "production";
}
