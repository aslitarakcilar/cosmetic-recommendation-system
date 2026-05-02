"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "../contexts/AuthContext";

export function Header() {
  const { user, logout } = useAuth();
  const router = useRouter();

  function handleLogout() {
    logout();
    router.push("/");
  }

  return (
    <header className="w-full border-b border-stone-200 bg-white/90 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link
          href="/"
          className="text-xs font-medium uppercase tracking-[0.25em] text-stone-800 hover:text-amber-700 transition-colors"
        >
          Cosmetic Intelligence
        </Link>

        <nav className="flex items-center gap-5">
          {user ? (
            <>
              <Link
                href="/explore"
                className="text-sm text-stone-600 hover:text-stone-900 transition-colors"
              >
                Keşfet
              </Link>
              <span className="text-xs text-stone-400 hidden sm:block max-w-[160px] truncate">
                {user.email}
              </span>
              <button
                onClick={handleLogout}
                className="text-sm text-stone-500 hover:text-stone-900 transition-colors"
              >
                Çıkış
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="text-sm text-stone-600 hover:text-stone-900 transition-colors"
              >
                Giriş yap
              </Link>
              <Link
                href="/register"
                className="text-sm bg-stone-900 text-white px-4 py-1.5 hover:bg-stone-700 transition-colors"
              >
                Kayıt ol
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
