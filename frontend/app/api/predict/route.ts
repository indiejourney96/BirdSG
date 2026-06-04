import { NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE_NAME } from "@/backend/auth/config";

export const runtime = "nodejs";

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

export async function POST(request: NextRequest) {
  const sessionToken = request.cookies.get(AUTH_COOKIE_NAME)?.value;

  if (!sessionToken) {
    return NextResponse.json({ detail: "Authentication required." }, { status: 401 });
  }

  const formData = await request.formData();

  const backendResponse = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    headers: {
      "x-birdsg-session": sessionToken,
    },
    body: formData,
  });

  return proxyResponse(backendResponse);
}
