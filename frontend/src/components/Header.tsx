"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "../contexts/AuthContext";

const NAV_ITEMS = [
  { href: "/explore", label: "Keşfet" },
  { href: "/profile", label: "Profilim" },
];

function isActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Header() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  function handleLogout() {
    logout();
    router.push("/");
  }

  return (
    <header className="sticky top-0 z-50 border-b border-[color:var(--border-strong)] bg-[rgba(255,253,249,0.82)] backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-3 md:px-6">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="flex items-center gap-3 rounded-full border border-white/80 bg-white/80 px-2 py-2 pr-4 shadow-sm transition-transform hover:-translate-y-0.5"
          >
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[linear-gradient(135deg,var(--accent),var(--accent-deep))] text-sm font-semibold text-white shadow-[0_10px_24px_rgba(198,137,66,0.35)]">
              CI
            </span>
            <span className="min-w-0">
              <span className="block text-[11px] uppercase tracking-[0.22em] text-stone-400">
                Sephora Thesis
              </span>
              <span className="block truncate text-sm font-medium text-stone-900">
                Cosmetic Intelligence
              </span>
            </span>
          </Link>
        </div>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <nav className="hidden items-center gap-2 md:flex">
                {NAV_ITEMS.map((item) => {
                  const active = isActive(pathname, item.href);
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`rounded-full px-4 py-2 text-sm transition-all ${
                        active
                          ? "bg-stone-900 text-white shadow-sm"
                          : "text-stone-600 hover:bg-white hover:text-stone-900"
                      }`}
                    >
                      {item.label}
                    </Link>
                  );
                })}
              </nav>

              <div className="hidden items-center gap-3 rounded-full border border-white/75 bg-white/80 px-3 py-2 shadow-sm sm:flex">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-stone-100 text-xs font-medium text-stone-700">
                  {user.email.slice(0, 2).toUpperCase()}
                </div>
                <div className="max-w-[180px]">
                  <p className="truncate text-xs font-medium text-stone-800">
                    {user.email}
                  </p>
                  <p className="text-[11px] text-stone-400">
                    Oturum aktif
                  </p>
                </div>
              </div>

              <button
                onClick={handleLogout}
                className="rounded-full border border-stone-200 bg-white px-4 py-2 text-sm text-stone-600 shadow-sm transition-colors hover:border-stone-400 hover:text-stone-900"
              >
                Çıkış
              </button>
            </>
          ) : (
            <nav className="flex items-center gap-2">
              <Link
                href="/login"
                className={`rounded-full px-4 py-2 text-sm transition-colors ${
                  pathname === "/login"
                    ? "bg-white text-stone-900 shadow-sm"
                    : "text-stone-600 hover:bg-white hover:text-stone-900"
                }`}
              >
                Giriş yap
              </Link>
              <Link
                href="/register"
                className={`rounded-full px-4 py-2 text-sm transition-all ${
                  pathname === "/register"
                    ? "bg-stone-900 text-white shadow-sm"
                    : "bg-stone-900 text-white hover:-translate-y-0.5 hover:bg-stone-700"
                }`}
              >
                Kayıt ol
              </Link>
            </nav>
          )}
        </div>
      </div>

      {user && (
        <nav className="mx-auto flex max-w-7xl gap-2 overflow-x-auto px-5 pb-3 md:hidden md:px-6">
          {NAV_ITEMS.map((item) => {
            const active = isActive(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`whitespace-nowrap rounded-full px-4 py-2 text-sm transition-all ${
                  active
                    ? "bg-stone-900 text-white shadow-sm"
                    : "border border-stone-200 bg-white text-stone-600"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      )}
    </header>
  );
}
