"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Home", icon: "home" },
  // { href: "/identify", label: "Identify", icon: "photo_camera" },
  { href: "/collection", label: "Collection", icon: "auto_awesome_motion" },
  { href: "#", label: "Settings", icon: "settings" },
] as const;

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 z-50 flex w-full items-center justify-around border-t border-outline-variant bg-surface px-4 pt-2 shadow-lg dark:border-outline dark:bg-surface-dim">
      {NAV_ITEMS.map((item) => {
        const isActive = item.href !== "#" && pathname === item.href;
        const activeClasses = isActive
          ? "bg-secondary-container text-on-secondary-container dark:bg-secondary dark:text-on-secondary px-5 py-1.5 scale-95"
          : "text-on-surface-variant dark:text-on-surface-variant py-1.5 hover:bg-surface-container dark:hover:bg-surface-container-high";

        return item.href === "#" ? (
          <span
            key={item.label}
            className="flex flex-col items-center justify-center rounded-full px-4 py-1.5 text-on-surface-variant opacity-70"
          >
            <span className="material-symbols-outlined">{item.icon}</span>
            <span className="font-label-sm text-label-sm">{item.label}</span>
          </span>
        ) : (
          <Link
            key={item.label}
            href={item.href}
            className={`flex flex-col items-center justify-center rounded-full transition-all duration-200 ${activeClasses}`}
          >
            <span
              className="material-symbols-outlined"
              style={{
                fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0",
              }}
            >
              {item.icon}
            </span>
            <span className="font-label-sm text-label-sm">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
