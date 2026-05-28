"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { LogOut, ShieldCheck } from "lucide-react";

type SessionUser = {
  id: string;
  email: string;
  lastLogin?: string | null;
};

export default function SessionToolbar() {
  const router = useRouter();
  const [user, setUser] = useState<SessionUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const response = await fetch("/api/auth/me", {
          credentials: "include",
          cache: "no-store",
        });

        if (!response.ok) {
          setUser(null);
          return;
        }

        const data = (await response.json()) as { authenticated: boolean; user?: SessionUser };

        if (data.authenticated && data.user) {
          setUser(data.user);
        }
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const handleLogout = async () => {
    setLoggingOut(true);

    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
      setUser(null);
      router.replace("/login");
      router.refresh();
    } finally {
      setLoggingOut(false);
    }
  };

  if (loading || !user) {
    return null;
  }

  return (
    <div className="mx-auto mb-4 flex max-w-screen-xl items-center justify-between gap-4 rounded-2xl border border-[#dce5d6] bg-white/80 px-4 py-3 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#154212]/10 text-[#154212]">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm font-semibold text-[#173118]">{user.email}</p>
          <p className="text-xs text-[#677264]">Secure session active</p>
        </div>
      </div>

      <button
        type="button"
        onClick={handleLogout}
        disabled={loggingOut}
        className="inline-flex items-center gap-2 rounded-xl bg-[#154212] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#1f5b1b] disabled:cursor-not-allowed disabled:opacity-70"
      >
        <LogOut className="h-4 w-4" />
        {loggingOut ? "Signing out..." : "Logout"}
      </button>
    </div>
  );
}
