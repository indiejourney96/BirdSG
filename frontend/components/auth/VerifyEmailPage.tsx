"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircle2 } from "lucide-react";

export default function VerifyEmailPage() {
  const [status, setStatus] = useState("Verifying...");
  const [error, setError] = useState("");

  useEffect(() => {
    const run = async () => {
      const token = new URLSearchParams(window.location.search).get("token") ?? "";
      const csrfResponse = await fetch("/api/auth/csrf", { credentials: "include", cache: "no-store" });
      const csrfData = (await csrfResponse.json()) as { csrfToken: string };

      if (!token) {
        setError("Missing verification token.");
        return;
      }

      const response = await fetch("/api/auth/verify-email", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfData.csrfToken },
        body: JSON.stringify({ token, csrfToken: csrfData.csrfToken }),
      });
      const data = (await response.json()) as { message?: string; error?: string };
      if (!response.ok) {
        setError(data.error ?? "Verification failed.");
        return;
      }
      setStatus(data.message ?? "Email verified.");
    };
    void run();
  }, []);

  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#f7fbf4_0%,#eef4e8_100%)] px-4 py-8 text-[#182017]">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-2xl items-center">
        <section className="w-full rounded-[2rem] border border-white/80 bg-white/90 p-8 text-center shadow-[0_24px_80px_rgba(21,44,20,0.12)]">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#154212]/10 text-[#154212]">
            <CheckCircle2 className="h-7 w-7" />
          </div>
          <h1 className="font-serif text-3xl text-[#163117]">Email verification</h1>
          <p className="mt-3 text-sm text-[#4e594b]">{error || status}</p>
          <Link href="/login" className="mt-6 inline-flex rounded-2xl bg-[#154212] px-5 py-3 text-sm font-semibold text-white">Go to login</Link>
        </section>
      </div>
    </main>
  );
}
