import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { AUTH_COOKIE_NAME } from "@/backend/auth/config";
import { readVerifiedSessionToken } from "@/backend/auth/session";
import LoginPage from "@/components/auth/LoginPage";

export default async function LoginRoutePage() {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(AUTH_COOKIE_NAME)?.value;
  const session = readVerifiedSessionToken(sessionToken);

  if (session) {
    redirect("/");
  }

  return <LoginPage />;
}
