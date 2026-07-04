type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null;
}

export function describeSupabaseError(error: unknown): string {
  if (!isRecord(error)) {
    return String(error);
  }

  const parts: string[] = [];

  for (const key of ["message", "code", "details", "hint", "name"]) {
    const value = error[key];
    if (typeof value === "string" && value.trim()) {
      parts.push(`${key}=${value}`);
    }
  }

  return parts.length > 0 ? parts.join(", ") : JSON.stringify(error);
}

export function getSupabaseErrorCode(error: unknown): string | null {
  if (!isRecord(error)) {
    return null;
  }

  const code = error.code;
  return typeof code === "string" && code.trim() ? code : null;
}
