"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Mail, ShieldAlert } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [csrfToken, setCsrfToken] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [devResetUrl, setDevResetUrl] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const response = await fetch("/api/auth/csrf", { credentials: "include", cache: "no-store" });
        const data = (await response.json()) as { csrfToken: string };
        setCsrfToken(data.csrfToken);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setMessage("");
    setDevResetUrl("");

    if (!email.trim()) {
      setError("Email address is required.");
      return;
    }

    setSubmitting(true);

    try {
      const response = await fetch("/api/auth/password-reset/request", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken,
        },
        body: JSON.stringify({ email }),
      });

      const data = (await response.json()) as { message?: string; error?: string; resetUrl?: string };

      if (!response.ok) {
        setError(data.error ?? "We could not process that request.");
        return;
      }

      setMessage(
        data.message ??
          "If an account exists, a password reset link has been generated and will be sent securely.",
      );

      if (data.resetUrl) {
        setDevResetUrl(data.resetUrl);
      }
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#f7fbf4_0%,#eef4e8_100%)] px-4 py-8 text-[#182017] sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-2xl items-center">
        <section className="w-full rounded-[2rem] border border-white/80 bg-white/90 p-6 shadow-[0_24px_80px_rgba(21,44,20,0.12)] backdrop-blur-xl sm:p-10">
          <Link href="/login" className="inline-flex items-center gap-2 text-sm font-medium text-[#0c6780]">
            <ArrowLeft className="h-4 w-4" />
            Back to login
          </Link>

          <div className="mt-6 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#154212]/10 text-[#154212]">
              <ShieldAlert className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#667160]">
                Secure reset
              </p>
              <h1 className="mt-1 font-serif text-3xl text-[#163117]">Request a password reset</h1>
            </div>
          </div>

          <p className="mt-4 max-w-xl text-sm leading-6 text-[#4e594b] sm:text-base">
            Enter the email tied to your BirdSG account. We return a generic response so no one can
            tell whether the address exists.
          </p>

          <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
            {error ? (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
                {error}
              </div>
            ) : null}

            {message ? (
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                {message}
              </div>
            ) : null}

            {devResetUrl ? (
              <div className="rounded-2xl border border-[#9ae1ff] bg-[#effaff] px-4 py-3 text-sm text-[#084253]">
                Development reset link:{" "}
                <a className="font-semibold underline" href={devResetUrl}>
                  open reset page
                </a>
              </div>
            ) : null}

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-[#364233]">Email address</span>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8b9688]" />
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="w-full rounded-2xl border border-[#d8dfd0] bg-white px-11 py-3.5 text-sm outline-none transition placeholder:text-[#98a596] focus:border-[#154212] focus:ring-4 focus:ring-[#154212]/10"
                  placeholder="name@example.com"
                />
              </div>
            </label>

            <button
              type="submit"
              disabled={loading || submitting}
              className="inline-flex w-full items-center justify-center rounded-2xl bg-[#154212] px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-[#1f5b1b] disabled:cursor-not-allowed disabled:opacity-70"
            >
              {submitting ? "Submitting..." : "Send reset link"}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
