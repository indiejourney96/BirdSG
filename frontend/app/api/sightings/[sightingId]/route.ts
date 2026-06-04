import { NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE_NAME } from "@/backend/auth/config";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const API_BASE_URL = process.env.BIRD_API_BASE_URL?.trim() ?? "http://127.0.0.1:8000";

async function proxyResponse(response: Response): Promise<NextResponse> {
  const body = await response.text();
  return new NextResponse(body, {
    status: response.status,
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
    },
  });
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ sightingId: string }> },
) {
  const sessionToken = request.cookies.get(AUTH_COOKIE_NAME)?.value;

  if (!sessionToken) {
    return NextResponse.json({ detail: "Authentication required." }, { status: 401 });
  }

  const { sightingId } = await context.params;
  const backendResponse = await fetch(`${API_BASE_URL}/sightings/${sightingId}`, {
    headers: {
      "x-birdsg-session": sessionToken,
    },
    cache: "no-store",
  });

  return proxyResponse(backendResponse);
}
