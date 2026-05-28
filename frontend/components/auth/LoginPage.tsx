"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  Feather,
  Lock,
  Mail,
  ShieldCheck,
  Sparkles,
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
    <main className="relative min-h-screen overflow-hidden bg-[#f4f7ef] text-[#1a231a]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(45,90,39,0.18),_transparent_32%),radial-gradient(circle_at_top_right,_rgba(12,103,128,0.14),_transparent_28%),linear-gradient(180deg,_#f8faf4_0%,_#eef3e8_100%)]" />
      <div className="absolute left-[-6rem] top-[-5rem] h-72 w-72 rounded-full bg-[#9ae1ff]/25 blur-3xl" />
      <div className="absolute bottom-[-5rem] right-[-4rem] h-80 w-80 rounded-full bg-[#bcf0ae]/25 blur-3xl" />

      <div className="relative mx-auto grid min-h-screen w-full max-w-7xl items-center gap-8 px-4 py-6 sm:px-6 lg:grid-cols-[1.08fr_0.92fr] lg:px-8">
        <section className="hidden overflow-hidden rounded-[2rem] border border-white/60 bg-[#14331f] text-white shadow-[0_30px_80px_rgba(18,33,18,0.2)] lg:flex lg:min-h-[760px] lg:flex-col lg:justify-between">
          <div className="relative p-10">
            <div className="mb-10 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/15 backdrop-blur-sm">
                <Feather className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-white/60">
                  SG BirdSpotter
                </p>
                <p className="text-sm text-white/70">Secure login for field observers</p>
              </div>
            </div>

            <div className="max-w-xl space-y-6">
              <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-4 py-2 text-sm text-white/80 backdrop-blur-sm">
                <Sparkles className="h-4 w-4" />
                Protected by Supabase, bcrypt, and httpOnly sessions
              </span>
              <h1 className="font-serif text-5xl leading-tight text-white">
                Welcome back to the
                <span className="block text-[#b7efad]">BirdSG observation hub</span>
              </h1>
              <p className="max-w-lg text-base leading-7 text-white/75">
                Sign in with email and password to access your bird identification tools,
                sightings, and analysis workbench. Sessions persist securely across refreshes,
                and login attempts are rate limited to keep the platform protected.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 border-t border-white/10 bg-black/10 p-6">
            {[
              { title: "Secure", text: "httpOnly session cookie" },
              { title: "Fast", text: "Remember me support" },
              { title: "Safe", text: "CSRF + rate limiting" },
            ].map((item) => (
              <article key={item.title} className="rounded-2xl border border-white/10 bg-white/8 p-4">
                <CheckCircle2 className="mb-3 h-5 w-5 text-[#b7efad]" />
                <h2 className="mb-1 text-sm font-semibold uppercase tracking-[0.16em] text-white/85">
                  {item.title}
                </h2>
                <p className="text-sm leading-6 text-white/70">{item.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="mx-auto w-full max-w-[560px] rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-[0_24px_80px_rgba(21,44,20,0.15)] backdrop-blur-xl sm:p-8">
          <div className="mb-6 flex items-start justify-between gap-4">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-[#154212]/6 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.22em] text-[#154212]">
                <ShieldCheck className="h-4 w-4" />
                Verified access only
              </div>
              <h2 className="font-serif text-3xl text-[#163117] sm:text-4xl">Sign in</h2>
              <p className="mt-2 max-w-md text-sm leading-6 text-[#4a5547] sm:text-base">
                Use your BirdSG credentials to continue. New accounts are provisioned with email
                verification before activation.
              </p>
            </div>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit} noValidate>
            {fieldErrors.general ? (
              <div
                role="alert"
                className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
              >
                {fieldErrors.general}
              </div>
            ) : null}

            {successMessage ? (
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                {successMessage}
              </div>
            ) : null}

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-[#364233]">Email address</span>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8b9688]" />
                <input
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
                  className="w-full rounded-2xl border border-[#d8dfd0] bg-white px-11 py-3.5 text-sm text-[#172016] outline-none transition placeholder:text-[#98a596] focus:border-[#154212] focus:ring-4 focus:ring-[#154212]/10"
                  placeholder="name@example.com"
                  aria-invalid={Boolean(fieldErrors.email)}
                  aria-describedby={fieldErrors.email ? "email-error" : undefined}
                />
              </div>
              {fieldErrors.email ? (
                <span id="email-error" className="mt-2 block text-sm text-rose-700">
                  {fieldErrors.email}
                </span>
              ) : null}
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-[#364233]">Password</span>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8b9688]" />
                <input
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
                  className="w-full rounded-2xl border border-[#d8dfd0] bg-white px-11 py-3.5 pr-14 text-sm text-[#172016] outline-none transition placeholder:text-[#98a596] focus:border-[#154212] focus:ring-4 focus:ring-[#154212]/10"
                  placeholder="Enter your password"
                  aria-invalid={Boolean(fieldErrors.password)}
                  aria-describedby={fieldErrors.password ? "password-error" : "password-help"}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((current) => !current)}
                  className="absolute right-3 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-xl text-[#6b7568] transition hover:bg-[#eef3e8] hover:text-[#154212]"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {fieldErrors.password ? (
                <span id="password-error" className="mt-2 block text-sm text-rose-700">
                  {fieldErrors.password}
                </span>
              ) : (
                <span id="password-help" className="mt-2 block text-sm text-[#667160]">
                  Password guidance: use at least 8 characters with upper and lower case, numbers,
                  and symbols for stronger protection.
                </span>
              )}

              <div className="mt-3 rounded-2xl border border-[#e4eadf] bg-[#f7faf4] p-3">
                <div className="mb-2 flex items-center justify-between text-xs font-semibold uppercase tracking-[0.18em] text-[#667160]">
                  <span>Password strength</span>
                  <span>{strength.label}</span>
                </div>
                <div className="h-2 rounded-full bg-[#dee6d7]">
                  <div
                    className={`h-2 rounded-full transition-all ${strength.colorClass}`}
                    style={{ width: `${Math.max(18, (strength.score / 4) * 100)}%` }}
                  />
                </div>
              </div>
            </label>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <label className="inline-flex items-center gap-3 text-sm text-[#425043]">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(event) => setRememberMe(event.target.checked)}
                  className="h-4 w-4 rounded border-[#c9d2c3] text-[#154212] focus:ring-[#154212]"
                />
                Remember me on this device
              </label>

              <Link
                href="/forgot-password"
                className="text-sm font-medium text-[#0c6780] transition hover:text-[#084253]"
              >
                Forgot password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={submitting || loadingCsrf}
              className="group inline-flex w-full items-center justify-center gap-3 rounded-2xl bg-[#154212] px-5 py-3.5 text-sm font-semibold text-white shadow-[0_18px_30px_rgba(21,66,18,0.22)] transition hover:bg-[#1f5b1b] disabled:cursor-not-allowed disabled:opacity-70"
            >
              {submitting || loadingCsrf ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/25 border-t-white" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign in
                  <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
                </>
              )}
            </button>

            <div className="rounded-2xl border border-dashed border-[#d8dfd0] bg-[#fbfcf8] px-4 py-4 text-sm leading-6 text-[#5a6657]">
              <p className="font-medium text-[#364233]">Email verification flow</p>
              <p className="mt-1">
                Signup is intentionally separated from login. New accounts should be created with
                an email-verification step before activation.
              </p>
            </div>
          </form>

          <div className="mt-6 flex items-center gap-4 text-sm text-[#6a7568]">
            <div className="h-px flex-1 bg-[#e1e7db]" />
            <span className="whitespace-nowrap">Need an account? Contact your administrator.</span>
            <div className="h-px flex-1 bg-[#e1e7db]" />
          </div>
        </section>
      </div>
    </main>
  );
}
