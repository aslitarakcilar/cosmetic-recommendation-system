"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { api, ApiError } from "../../lib/api";

const SKIN_TYPES = [
  { value: "dry", label: "Kuru" },
  { value: "oily", label: "Yağlı" },
  { value: "combination", label: "Karma" },
  { value: "normal", label: "Normal" },
  { value: "sensitive", label: "Hassas" },
];

const SKIN_TONES = [
  { value: "fair", label: "Çok açık" },
  { value: "light", label: "Açık" },
  { value: "medium", label: "Orta" },
  { value: "tan", label: "Buğday" },
  { value: "dark", label: "Koyu" },
  { value: "rich", label: "Zengin koyu" },
  { value: "deep", label: "Derin" },
];

const UNDERTONES = [
  { value: "warm", label: "Sıcak" },
  { value: "cool", label: "Soğuk" },
  { value: "neutral", label: "Nötr" },
  { value: "olive", label: "Zeytinyağı" },
];

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <label className="text-xs uppercase tracking-[0.15em] text-stone-500">
        {label}
      </label>
      {children}
      {error && <span className="text-xs text-red-500">{error}</span>}
    </div>
  );
}

const INPUT_CLS =
  "rounded-2xl border border-stone-200 bg-stone-50/80 px-4 py-3 text-sm text-stone-800 placeholder-stone-300 outline-none transition-colors focus:border-stone-700";
const SELECT_CLS =
  "rounded-2xl border border-stone-200 bg-stone-50/80 px-4 py-3 text-sm text-stone-800 outline-none transition-colors focus:border-stone-700";

type FormErrors = Partial<Record<
  "email" | "password" | "skin_type" | "skin_tone" | "undertone" | "general",
  string
>>;

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [form, setForm] = useState({
    email: "",
    password: "",
    skin_type: "",
    skin_tone: "",
    undertone: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);

  function set(key: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      setForm((prev) => ({ ...prev, [key]: e.target.value }));
      setErrors((prev) => ({ ...prev, [key]: undefined }));
    };
  }

  function validate(): FormErrors {
    const nextErrors: FormErrors = {};
    if (!form.email) nextErrors.email = "E-posta gerekli.";
    if (!form.password || form.password.length < 6) {
      nextErrors.password = "Şifre en az 6 karakter olmalı.";
    }
    if (!form.skin_type) nextErrors.skin_type = "Cilt tipi seçiniz.";
    if (!form.skin_tone) nextErrors.skin_tone = "Cilt tonu seçiniz.";
    if (!form.undertone) nextErrors.undertone = "Alt ton seçiniz.";
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
      await api.register(form);
      const tokenRes = await api.login(form.email, form.password);
      await login(tokenRes.access_token);
      router.push("/explore");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Kayıt başarısız.";
      setErrors({ general: message });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto min-h-[calc(100vh-3.5rem)] max-w-7xl px-5 py-8 md:px-6 md:py-10">
      <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="overflow-hidden rounded-[2rem] border border-[color:var(--border-strong)] bg-[linear-gradient(135deg,rgba(255,255,255,0.9),rgba(246,236,224,0.95))] px-6 py-7 shadow-[0_24px_60px_rgba(28,25,23,0.06)] md:px-8 md:py-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/80 bg-white/75 px-3 py-1 text-[11px] uppercase tracking-[0.22em] text-stone-500 shadow-sm">
            <span className="h-2 w-2 rounded-full bg-[var(--accent)]" />
            Yeni kullanıcı akışı
          </div>

          <h1 className="mt-6 max-w-xl text-3xl font-light leading-tight text-stone-900 md:text-4xl">
            Cilt profilinle başlayan
            <span className="block text-[color:var(--accent-deep)]">
              kişisel bir öneri hesabı oluştur
            </span>
          </h1>
          <p className="mt-4 max-w-xl text-sm leading-7 text-stone-600">
            İlk günden isabetli öneriler üretebilmek için cilt bilgilerini kullanıyoruz.
            Daha sonra puanlamaların geldikçe sistem davranış verinle birlikte çalışıyor.
          </p>

          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
              <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                Aşama 1
              </p>
              <p className="mt-2 text-sm font-medium text-stone-900">Profil eşleşmesi</p>
              <p className="mt-1 text-xs leading-6 text-stone-500">
                Cilt tipi, tonu ve alt ton başlangıç sinyali olur.
              </p>
            </div>
            <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
              <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                Aşama 2
              </p>
              <p className="mt-2 text-sm font-medium text-stone-900">İçerik benzerliği</p>
              <p className="mt-1 text-xs leading-6 text-stone-500">
                Puanladığın ürünlere yakın seçenekler öne çıkar.
              </p>
            </div>
            <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
              <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                Aşama 3
              </p>
              <p className="mt-2 text-sm font-medium text-stone-900">Hybrid güç</p>
              <p className="mt-1 text-xs leading-6 text-stone-500">
                Davranış ve kategori sinyalleri birlikte dengelenir.
              </p>
            </div>
          </div>
        </section>

        <section className="rounded-[2rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-6 py-7 shadow-[0_24px_60px_rgba(28,25,23,0.06)] md:px-8 md:py-8">
          <div className="mb-6">
            <p className="text-xs uppercase tracking-[0.22em] text-stone-400">
              Hesap oluştur
            </p>
            <p className="mt-3 text-sm leading-7 text-stone-500">
              Birkaç alan doldurman yeterli. Sonrasında keşfet ekranında kişiselleştirilmiş
              ürünleri hemen görebilirsin.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
            <Field label="E-posta" error={errors.email}>
              <input
                type="email"
                value={form.email}
                onChange={set("email")}
                placeholder="ornek@email.com"
                className={INPUT_CLS}
              />
            </Field>

            <Field label="Şifre" error={errors.password}>
              <input
                type="password"
                value={form.password}
                onChange={set("password")}
                placeholder="En az 6 karakter"
                className={INPUT_CLS}
              />
            </Field>

            <div className="rounded-[1.5rem] border border-stone-200 bg-stone-50/70 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-stone-400">
                Cilt profili
              </p>
              <div className="mt-4 flex flex-col gap-4">
                <Field label="Cilt tipi" error={errors.skin_type}>
                  <select
                    value={form.skin_type}
                    onChange={set("skin_type")}
                    className={SELECT_CLS}
                  >
                    <option value="">Seçiniz…</option>
                    {SKIN_TYPES.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </Field>

                <Field label="Cilt tonu" error={errors.skin_tone}>
                  <select
                    value={form.skin_tone}
                    onChange={set("skin_tone")}
                    className={SELECT_CLS}
                  >
                    <option value="">Seçiniz…</option>
                    {SKIN_TONES.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </Field>

                <Field label="Cilt alt tonu" error={errors.undertone}>
                  <select
                    value={form.undertone}
                    onChange={set("undertone")}
                    className={SELECT_CLS}
                  >
                    <option value="">Seçiniz…</option>
                    {UNDERTONES.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>
            </div>

            {errors.general && (
              <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                {errors.general}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="mt-1 rounded-2xl bg-stone-900 py-3 text-sm uppercase tracking-[0.2em] text-white transition-all hover:-translate-y-0.5 hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? "Hesap oluşturuluyor…" : "Hesap oluştur"}
            </button>
          </form>

          <p className="mt-6 text-sm text-stone-500">
            Zaten hesabın var mı?{" "}
            <Link
              href="/login"
              className="font-medium text-stone-900 underline underline-offset-2 hover:text-[color:var(--accent-deep)]"
            >
              Giriş yap
            </Link>
          </p>
        </section>
      </div>
    </div>
  );
}
