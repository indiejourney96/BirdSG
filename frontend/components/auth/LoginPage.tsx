"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  Eye,
  EyeOff,
  Lock,
  Mail,
} from "lucide-react";

type FieldErrors = Partial<{
  email: string;
  password: string;
  csrfToken: string;
  general: string;
}>;

type PasswordStrength = {
  score: number;
  label: string;
  colorClass: string;
};

function getPasswordStrength(password: string): PasswordStrength {
  let score = 0;

  if (password.length >= 8) score += 1;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;

  if (score <= 1) {
    return { score, label: "Weak", colorClass: "bg-rose-500" };
  }

  if (score === 2 || score === 3) {
    return { score, label: "Fair", colorClass: "bg-amber-500" };
  }

  return { score, label: "Strong", colorClass: "bg-emerald-500" };
}

export default function LoginPage() {
  const router = useRouter();
  const [csrfToken, setCsrfToken] = useState("");
  const [loadingCsrf, setLoadingCsrf] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [successMessage, setSuccessMessage] = useState("");

  const strength = useMemo(() => getPasswordStrength(password), [password]);

  useEffect(() => {
    const loadCsrf = async () => {
      try {
        const response = await fetch("/api/auth/csrf", {
          method: "GET",
          credentials: "include",
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error("Unable to prepare login session.");
        }

        const data = (await response.json()) as { csrfToken: string };
        setCsrfToken(data.csrfToken);
      } catch {
        setFieldErrors((current) => ({
          ...current,
          general: "We could not prepare the login form. Please refresh and try again.",
        }));
      } finally {
        setLoadingCsrf(false);
      }
    };

    void loadCsrf();
  }, []);

  const validateForm = (): boolean => {
    const nextErrors: FieldErrors = {};
    const trimmedEmail = email.trim().toLowerCase();

    if (!trimmedEmail) {
      nextErrors.email = "Email address is required.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      nextErrors.email = "Enter a valid email address.";
    }

    if (!password) {
      nextErrors.password = "Password is required.";
    }

    if (!csrfToken) {
      nextErrors.csrfToken = "Security token is missing. Refresh the page and try again.";
    }

    setFieldErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSuccessMessage("");

    if (!validateForm()) {
      return;
    }

    setSubmitting(true);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken,
        },
        body: JSON.stringify({
          email,
          password,
          rememberMe,
          csrfToken,
        }),
      });

      if (response.ok) {
        setSuccessMessage("Login successful. Redirecting...");
        router.replace("/");
        router.refresh();
        return;
      }

      if (response.status === 429) {
        setFieldErrors({
          general: "Too many login attempts. Please wait 15 minutes and try again.",
        });
        return;
      }

      if (response.status === 401 || response.status === 400) {
        setFieldErrors({
          general: "Invalid email or password.",
        });
        return;
      }

      setFieldErrors({
        general: "We could not sign you in right now. Please try again.",
      });
    } catch {
      setFieldErrors({
        general: "Network error. Please check your connection and try again.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-b from-[#f8faf4] to-[#eef3e8] px-4 py-12 text-[#1a231a] sm:px-6 lg:px-8">
      {/* Structural Minimal Background Orbs */}
      <div className="pointer-events-none absolute left-[-4rem] top-[-4rem] h-80 w-80 rounded-full bg-[#9ae1ff]/15 blur-3xl" />
      <div className="pointer-events-none absolute bottom-[-4rem] right-[-4rem] h-96 w-96 rounded-full bg-[#bcf0ae]/20 blur-3xl" />

      <div className="relative w-full max-w-[460px]">
        <section className="w-full rounded-3xl border border-white/80 bg-white/90 p-6 shadow-[0_20px_60px_rgba(21,44,20,0.06)] backdrop-blur-xl sm:p-8">
          
          {/* Aligned Header Elements */}
          <div className="mb-8 flex flex-col items-center text-center">
            <div className="relative mb-4 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-b from-white to-[#f4f7ef] p-1 shadow-sm ring-1 ring-[#e4eadf]">
              <img
                src="/images/logo.png"
                alt="BirdSG Logo"
                className="h-full w-full object-contain"
              />
            </div>
            <h2 className="font-serif text-3xl font-medium tracking-tight text-[#163117]">
              Welcome Bird Watchers
            </h2>
            <p className="mt-1.5 text-sm text-[#667160]">
              Sign in to map your local Singapore avian encounters.
            </p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit} noValidate>
            {fieldErrors.general && (
              <div
                role="alert"
                className="rounded-xl border border-rose-100 bg-rose-50/80 px-4 py-3 text-xs font-medium text-rose-800"
              >
                {fieldErrors.general}
              </div>
            )}

            {successMessage && (
              <div className="rounded-xl border border-emerald-100 bg-emerald-50/80 px-4 py-3 text-xs font-medium text-emerald-800">
                {successMessage}
              </div>
            )}

            {/* Email Field Block */}
            <div className="space-y-1.5">
              <label htmlFor="email" className="text-xs font-bold uppercase tracking-wider text-[#364233]">
                Email address
              </label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8b9688]" />
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  inputMode="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  onBlur={() => {
                    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
                      setFieldErrors((current) => ({
                        ...current,
                        email: "Enter a valid email address.",
                      }));
                    }
                  }}
                  className="w-full rounded-xl border border-[#d8dfd0] bg-white px-11 py-3 text-sm text-[#172016] outline-none transition placeholder:text-[#98a596] focus:border-[#154212] focus:ring-4 focus:ring-[#154212]/5"
                  placeholder="name@example.com"
                  aria-invalid={Boolean(fieldErrors.email)}
                  aria-describedby={fieldErrors.email ? "email-error" : undefined}
                />
              </div>
              {fieldErrors.email && (
                <span id="email-error" className="block text-xs font-medium text-rose-600 mt-1">
                  {fieldErrors.email}
                </span>
              )}
            </div>

            {/* Password Field Block */}
            <div className="space-y-1.5">
              <label htmlFor="password" className="text-xs font-bold uppercase tracking-wider text-[#364233]">
                Password
              </label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8b9688]" />
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  onBlur={() => {
                    if (!password) {
                      setFieldErrors((current) => ({
                        ...current,
                        password: "Password is required.",
                      }));
                    }
                  }}
                  className="w-full rounded-xl border border-[#d8dfd0] bg-white px-11 py-3 pr-12 text-sm text-[#172016] outline-none transition placeholder:text-[#98a596] focus:border-[#154212] focus:ring-4 focus:ring-[#154212]/5"
                  placeholder="Enter your password"
                  aria-invalid={Boolean(fieldErrors.password)}
                  aria-describedby={fieldErrors.password ? "password-error" : "password-help"}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((current) => !current)}
                  className="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-lg text-[#6b7568] transition hover:bg-[#eef3e8] hover:text-[#154212]"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              
              {fieldErrors.password ? (
                <span id="password-error" className="block text-xs font-medium text-rose-600 mt-1">
                  {fieldErrors.password}
                </span>
              ) : (
                <span id="password-help" className="block text-[11px] leading-normal text-[#667160] mt-1">
                  Must contain 8+ characters, mixed cases, numbers, and symbols.
                </span>
              )}

              {/* Strength Progress Tracker */}
              <div className="mt-3 rounded-xl border border-[#e4eadf] bg-[#f7faf4] p-3">
                <div className="mb-1.5 flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-[#667160]">
                  <span>Password strength</span>
                  <span className="font-semibold">{strength.label}</span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-[#dee6d7] overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${strength.colorClass}`}
                    style={{ width: `${Math.max(12, (strength.score / 4) * 100)}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Checkbox and Sub-actions row */}
            <div className="flex items-center justify-between pt-1">
              <label className="inline-flex cursor-pointer select-none items-center gap-2">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(event) => setRememberMe(event.target.checked)}
                  className="h-4 w-4 rounded border-[#c9d2c3] text-[#154212] focus:ring-[#154212] focus:ring-offset-0"
                />
                <span className="text-xs font-medium text-[#425043]">Remember me</span>
              </label>

              <Link
                href="/forgot-password"
                className="text-xs font-semibold text-[#154212] hover:underline"
              >
                Forgot password?
              </Link>
            </div>

            {/* Form Execution Handler */}
            <button
              type="submit"
              disabled={submitting || loadingCsrf}
              className="group flex w-full items-center justify-center gap-2.5 rounded-xl bg-[#154212] py-3 text-sm font-semibold text-white shadow-md transition-all hover:bg-[#0f300d] focus:outline-none focus:ring-4 focus:ring-[#154212]/20 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-70"
            >
              {submitting || loadingCsrf ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/25 border-t-white" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign In
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                </>
              )}
            </button>
          </form>

          {/* Clean Segment Divider Footer */}
          <div className="mt-8 flex items-center gap-4 text-xs text-[#6a7568]">
            <div className="h-px flex-1 bg-[#e1e7db]" />
            <span className="whitespace-nowrap text-[#667160]">
              New here?{" "}
              <Link href="/signup" className="font-semibold text-[#154212] hover:underline">
                Create an account
              </Link>
            </span>
            <div className="h-px flex-1 bg-[#e1e7db]" />
          </div>

        </section>
      </div>
    </main>
  );
}