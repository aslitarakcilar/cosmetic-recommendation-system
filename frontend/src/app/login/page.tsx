"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { api, ApiError } from "../../lib/api";

const INPUT_CLS =
  "border-b border-stone-300 bg-transparent py-2.5 text-sm text-stone-800 placeholder-stone-300 outline-none focus:border-stone-700 transition-colors";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string; general?: string }>({});
  const [submitting, setSubmitting] = useState(false);

  function validate() {
    const e: typeof errors = {};
    if (!email) e.email = "E-posta gerekli.";
    if (!password) e.password = "Şifre gerekli.";
    return e;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setSubmitting(true);
    setErrors({});
    try {
      const res = await api.login(email, password);
      await login(res.access_token);
      router.push("/explore");
    } catch (err) {
      setErrors({
        general: err instanceof ApiError ? err.message : "Giriş başarısız.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <h1 className="text-3xl font-light text-stone-900 mb-1">Giriş yap</h1>
        <p className="text-sm text-stone-500 mb-8">
          Kişiselleştirilmiş önerilere erişmek için giriş yap.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
          <div className="flex flex-col gap-1">
            <label className="text-xs uppercase tracking-[0.15em] text-stone-500">
              E-posta
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setErrors((p) => ({ ...p, email: undefined })); }}
              placeholder="ornek@email.com"
              className={INPUT_CLS}
            />
            {errors.email && <span className="text-xs text-red-500">{errors.email}</span>}
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs uppercase tracking-[0.15em] text-stone-500">
              Şifre
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setErrors((p) => ({ ...p, password: undefined })); }}
              className={INPUT_CLS}
            />
            {errors.password && <span className="text-xs text-red-500">{errors.password}</span>}
          </div>

          {errors.general && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 px-3 py-2 rounded">
              {errors.general}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="mt-2 bg-stone-900 text-white py-3 text-sm uppercase tracking-widest hover:bg-stone-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? "Giriş yapılıyor…" : "Giriş yap"}
          </button>
        </form>

        <p className="mt-5 text-sm text-stone-500">
          Hesabın yok mu?{" "}
          <Link
            href="/register"
            className="text-stone-800 underline underline-offset-2 hover:text-amber-700"
          >
            Kayıt ol
          </Link>
        </p>
      </div>
    </div>
  );
}
