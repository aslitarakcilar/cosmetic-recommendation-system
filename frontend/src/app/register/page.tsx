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
    <div className="flex flex-col gap-1">
      <label className="text-xs uppercase tracking-[0.15em] text-stone-500">
        {label}
      </label>
      {children}
      {error && <span className="text-xs text-red-500">{error}</span>}
    </div>
  );
}

const INPUT_CLS =
  "border-b border-stone-300 bg-transparent py-2.5 text-sm text-stone-800 placeholder-stone-300 outline-none focus:border-stone-700 transition-colors";
const SELECT_CLS =
  "border-b border-stone-300 bg-transparent py-2.5 text-sm text-stone-800 outline-none focus:border-stone-700 transition-colors";

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
    const e: FormErrors = {};
    if (!form.email) e.email = "E-posta gerekli.";
    if (!form.password || form.password.length < 6)
      e.password = "Şifre en az 6 karakter olmalı.";
    if (!form.skin_type) e.skin_type = "Cilt tipi seçiniz.";
    if (!form.skin_tone) e.skin_tone = "Cilt tonu seçiniz.";
    if (!form.undertone) e.undertone = "Alt ton seçiniz.";
    return e;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) {
      setErrors(errs);
      return;
    }

    setSubmitting(true);
    setErrors({});

    try {
      await api.register(form);
      const token_res = await api.login(form.email, form.password);
      await login(token_res.access_token);
      router.push("/explore");
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Kayıt başarısız.";
      setErrors({ general: msg });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex">
      {/* ── Form paneli ───────────────────────────────────── */}
      <div className="w-full md:w-1/2 flex flex-col justify-center px-8 md:px-14 py-14">
        <div className="max-w-sm w-full mx-auto md:mx-0">
          <h1 className="text-3xl font-light text-stone-900 mb-1">Kayıt ol</h1>
          <p className="text-sm text-stone-500 mb-8">
            Cilt profilin, yeni kullanıcı olarak sana uygun ürünleri bulmak
            için kullanılır.
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
            {/* E-posta */}
            <Field label="E-posta" error={errors.email}>
              <input
                type="email"
                value={form.email}
                onChange={set("email")}
                placeholder="ornek@email.com"
                className={INPUT_CLS}
              />
            </Field>

            {/* Şifre */}
            <Field label="Şifre" error={errors.password}>
              <input
                type="password"
                value={form.password}
                onChange={set("password")}
                placeholder="En az 6 karakter"
                className={INPUT_CLS}
              />
            </Field>

            {/* Cilt profili başlığı */}
            <div className="pt-3 border-t border-stone-100">
              <p className="text-xs uppercase tracking-[0.15em] text-stone-400 mb-4">
                Cilt profili
              </p>

              <div className="flex flex-col gap-5">
                {/* Cilt tipi */}
                <Field label="Cilt tipi" error={errors.skin_type}>
                  <select
                    value={form.skin_type}
                    onChange={set("skin_type")}
                    className={SELECT_CLS}
                  >
                    <option value="">Seçiniz…</option>
                    {SKIN_TYPES.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </Field>

                {/* Cilt tonu */}
                <Field label="Cilt tonu" error={errors.skin_tone}>
                  <select
                    value={form.skin_tone}
                    onChange={set("skin_tone")}
                    className={SELECT_CLS}
                  >
                    <option value="">Seçiniz…</option>
                    {SKIN_TONES.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </Field>

                {/* Alt ton */}
                <Field label="Cilt alt tonu" error={errors.undertone}>
                  <select
                    value={form.undertone}
                    onChange={set("undertone")}
                    className={SELECT_CLS}
                  >
                    <option value="">Seçiniz…</option>
                    {UNDERTONES.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>
            </div>

            {/* Genel hata */}
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
              {submitting ? "Hesap oluşturuluyor…" : "Hesap oluştur"}
            </button>
          </form>

          <p className="mt-5 text-sm text-stone-500">
            Zaten hesabın var mı?{" "}
            <Link
              href="/login"
              className="text-stone-800 underline underline-offset-2 hover:text-amber-700"
            >
              Giriş yap
            </Link>
          </p>
        </div>
      </div>

      {/* ── Bilgi paneli ────────────────────────────────────── */}
      <div className="hidden md:flex md:w-1/2 bg-stone-900 text-white flex-col justify-center px-14">
        <p className="text-xs uppercase tracking-[0.2em] text-stone-500 mb-8">
          Nasıl çalışır?
        </p>
        <div className="flex flex-col gap-7">
          {[
            [
              "Profil tabanlı (yeni kullanıcı)",
              "Cilt tipine ve tonuna göre, aynı profile sahip kullanıcıların yüksek puan verdiği ürünler önerilir. Hiç geçmiş gerekmez.",
            ],
            [
              "İçerik tabanlı (≥3 puanlama)",
              "Beğendiğin ürünlere benzer ürünler TF-IDF metin benzerliğiyle bulunur.",
            ],
            [
              "Hybrid (Sephora geçmişi)",
              "Verisetindeki geçmişin varsa, collaborative filtering + içerik reranking ile en güçlü kişiselleştirme aktif olur.",
            ],
          ].map(([title, desc]) => (
            <div key={title}>
              <h3 className="text-sm font-medium text-white mb-1">{title}</h3>
              <p className="text-sm text-stone-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
