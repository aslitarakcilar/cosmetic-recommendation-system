"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { api, ApiError } from "../../lib/api";

const INPUT_CLS =
  "rounded-2xl border border-stone-200 bg-stone-50/80 px-4 py-3 text-sm text-stone-800 placeholder-stone-300 outline-none transition-colors focus:border-stone-700";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{
    email?: string;
    password?: string;
    general?: string;
  }>({});
  const [submitting, setSubmitting] = useState(false);

  function validate() {
    const nextErrors: typeof errors = {};
    if (!email) nextErrors.email = "E-posta gerekli.";
    if (!password) nextErrors.password = "Şifre gerekli.";
    return nextErrors;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const nextErrors = validate();
    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors);
      return;
    }

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
    <div className="mx-auto min-h-[calc(100vh-3.5rem)] max-w-7xl px-5 py-8 md:px-6 md:py-10">
      <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <section className="rounded-[2rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-6 py-7 shadow-[0_24px_60px_rgba(28,25,23,0.06)] md:px-8 md:py-8">
          <div className="mb-8">
            <p className="text-xs uppercase tracking-[0.22em] text-stone-400">
              Hesabına dön
            </p>
            <h1 className="mt-3 text-3xl font-light text-stone-900 md:text-4xl">
              Kişiselleştirilmiş önerilerine tekrar ulaş
            </h1>
            <p className="mt-3 max-w-md text-sm leading-7 text-stone-500">
              Profilin, puanlamaların ve keşif geçmişin seni bekliyor. Giriş
              yaptıktan sonra öneri akışı kaldığın yerden devam eder.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
            <div className="flex flex-col gap-2">
              <label className="text-xs uppercase tracking-[0.15em] text-stone-500">
                E-posta
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setErrors((prev) => ({ ...prev, email: undefined }));
                }}
                placeholder="ornek@email.com"
                className={INPUT_CLS}
              />
              {errors.email && <span className="text-xs text-red-500">{errors.email}</span>}
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs uppercase tracking-[0.15em] text-stone-500">
                Şifre
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setErrors((prev) => ({ ...prev, password: undefined }));
                }}
                placeholder="Şifreni gir"
                className={INPUT_CLS}
              />
              {errors.password && (
                <span className="text-xs text-red-500">{errors.password}</span>
              )}
            </div>

            {errors.general && (
              <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                {errors.general}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="mt-2 rounded-2xl bg-stone-900 py-3 text-sm uppercase tracking-[0.2em] text-white transition-all hover:-translate-y-0.5 hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? "Giriş yapılıyor…" : "Giriş yap"}
            </button>
          </form>

          <p className="mt-6 text-sm text-stone-500">
            Hesabın yok mu?{" "}
            <Link
              href="/register"
              className="font-medium text-stone-900 underline underline-offset-2 hover:text-[color:var(--accent-deep)]"
            >
              Kayıt ol
            </Link>
          </p>
        </section>

        <section className="overflow-hidden rounded-[2rem] border border-[color:var(--border-strong)] bg-[linear-gradient(135deg,rgba(255,255,255,0.88),rgba(246,236,224,0.95))] px-6 py-7 shadow-[0_24px_60px_rgba(28,25,23,0.06)] md:px-8 md:py-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/80 bg-white/75 px-3 py-1 text-[11px] uppercase tracking-[0.22em] text-stone-500 shadow-sm">
            <span className="h-2 w-2 rounded-full bg-[var(--accent)]" />
            Öneri motoru aktif
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
              <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                Veri temeli
              </p>
              <p className="mt-2 text-lg font-light text-stone-900">8.494</p>
              <p className="mt-1 text-xs text-stone-500">ürün profili</p>
            </div>
            <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
              <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                İçgörü
              </p>
              <p className="mt-2 text-lg font-light text-stone-900">1M+</p>
              <p className="mt-1 text-xs text-stone-500">yorum sinyali</p>
            </div>
            <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
              <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                Model
              </p>
              <p className="mt-2 text-lg font-light text-stone-900">Hybrid</p>
              <p className="mt-1 text-xs text-stone-500">çok katmanlı seçim</p>
            </div>
          </div>

          <div className="mt-8 space-y-4">
            {[
              [
                "Yeni kullanıcı başlangıcı",
                "Profil bilgilerinle cilt tipine ve tonuna uygun ürünler önceliklenir.",
              ],
              [
                "Davranış ile güçlenir",
                "Puanlama yaptıkça içerik ve collaborative filtering sinyalleri devreye girer.",
              ],
              [
                "Kategori bazlı netlik",
                "Her keşif isteğinde kategori bağlamı korunur; öneriler daha odaklı gelir.",
              ],
            ].map(([title, description]) => (
              <div
                key={title}
                className="rounded-[1.5rem] border border-white/65 bg-white/70 p-5 shadow-sm"
              >
                <p className="text-sm font-medium text-stone-900">{title}</p>
                <p className="mt-2 text-sm leading-7 text-stone-600">
                  {description}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
