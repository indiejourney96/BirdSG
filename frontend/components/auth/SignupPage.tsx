"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, Eye, EyeOff, Lock, Mail, UserPlus } from "lucide-react";

type FieldErrors = Partial<{
  email: string;
  password: string;
  confirmPassword: string;
  general: string;
}>;

function passwordScore(password: string): string {
  let score = 0;
  if (password.length >= 8) score += 1;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;
  return score >= 4 ? "Strong" : score >= 2 ? "Fair" : "Weak";
}

export default function SignupPage() {
  const [csrfToken, setCsrfToken] = useState("");
  const [loadingCsrf, setLoadingCsrf] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [message, setMessage] = useState("");
  const strengthLabel = useMemo(() => passwordScore(password), [password]);

  useEffect(() => {
    const load = async () => {
      const response = await fetch("/api/auth/csrf", { credentials: "include", cache: "no-store" });
      const data = (await response.json()) as { csrfToken: string };
      setCsrfToken(data.csrfToken);
      setLoadingCsrf(false);
    };
    void load();
  }, []);

  const validate = (): boolean => {
    const nextErrors: FieldErrors = {};
    if (!email.trim()) nextErrors.email = "Email is required.";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) nextErrors.email = "Enter a valid email address.";
    if (!password) nextErrors.password = "Password is required.";
    if (password !== confirmPassword) nextErrors.confirmPassword = "Passwords do not match.";
    setFieldErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setMessage("");
    if (!validate() || !csrfToken) return;
    setSubmitting(true);

    try {
      const response = await fetch("/api/auth/signup", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
        body: JSON.stringify({ email, password, confirmPassword, csrfToken }),
      });
      const data = (await response.json()) as { error?: string; message?: string; verificationUrl?: string };

      if (!response.ok) {
        setFieldErrors({ general: data.error ?? "We could not create your account." });
        return;
      }

      setMessage(data.message ?? "Account created. Check your email to verify it.");
      if (data.verificationUrl) {
        setMessage(`${data.message ?? "Account created."} Dev link: ${data.verificationUrl}`);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#f7fbf4_0%,#eef4e8_100%)] px-4 py-8 text-[#182017] sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-2xl items-center">
        <section className="w-full rounded-[2rem] border border-white/80 bg-white/90 p-6 shadow-[0_24px_80px_rgba(21,44,20,0.12)] backdrop-blur-xl sm:p-10">
          <Link href="/login" className="text-sm font-medium text-[#0c6780]">Back to login</Link>
          <div className="mt-6 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#154212]/10 text-[#154212]">
              <UserPlus className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#667160]">Create account</p>
              <h1 className="mt-1 font-serif text-3xl text-[#163117]">Sign up</h1>
            </div>
          </div>
          <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
            {fieldErrors.general ? <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{fieldErrors.general}</div> : null}
            {message ? <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{message}</div> : null}
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-[#364233]">Email address</span>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8b9688]" />
                <input className="w-full rounded-2xl border border-[#d8dfd0] bg-white px-11 py-3.5 text-sm outline-none focus:border-[#154212] focus:ring-4 focus:ring-[#154212]/10" value={email} onChange={(e) => setEmail(e.target.value)} type="email" />
              </div>
              {fieldErrors.email ? <span className="mt-2 block text-sm text-rose-700">{fieldErrors.email}</span> : null}
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-[#364233]">Password</span>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8b9688]" />
                <input className="w-full rounded-2xl border border-[#d8dfd0] bg-white px-11 py-3.5 pr-14 text-sm outline-none focus:border-[#154212] focus:ring-4 focus:ring-[#154212]/10" value={password} onChange={(e) => setPassword(e.target.value)} type={showPassword ? "text" : "password"} />
                <button type="button" onClick={() => setShowPassword((v) => !v)} className="absolute right-3 top-1/2 h-9 w-9 -translate-y-1/2 rounded-xl text-[#6b7568]">
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <span className="mt-2 block text-sm text-[#667160]">Password strength: {strengthLabel}</span>
              {fieldErrors.password ? <span className="mt-2 block text-sm text-rose-700">{fieldErrors.password}</span> : null}
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-[#364233]">Confirm password</span>
              <input className="w-full rounded-2xl border border-[#d8dfd0] bg-white px-4 py-3.5 text-sm outline-none focus:border-[#154212] focus:ring-4 focus:ring-[#154212]/10" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} type="password" />
              {fieldErrors.confirmPassword ? <span className="mt-2 block text-sm text-rose-700">{fieldErrors.confirmPassword}</span> : null}
            </label>
            <button type="submit" disabled={submitting || loadingCsrf} className="inline-flex w-full items-center justify-center gap-3 rounded-2xl bg-[#154212] px-5 py-3.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-70">
              {submitting ? "Creating account..." : <>Create account <ArrowRight className="h-4 w-4" /></>}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
