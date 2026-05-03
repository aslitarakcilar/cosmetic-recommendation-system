"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import {
  api,
  ApiError,
  type RatedProductDetail,
} from "../../lib/api";
import { toTitleCase } from "../../lib/utils";

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

const STARS = [1, 2, 3, 4, 5];

function ProfileRatingsSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: 3 }).map((_, index) => (
        <div
          key={index}
          className="rounded-[1.75rem] border border-stone-200 bg-stone-50/50 p-5"
        >
          <div className="space-y-4">
            <div className="flex items-start justify-between gap-3">
              <div className="w-full space-y-2">
                <div className="skeleton h-3 w-24 rounded-full" />
                <div className="skeleton h-5 w-4/5 rounded-full" />
                <div className="skeleton h-4 w-1/2 rounded-full" />
              </div>
              <div className="skeleton h-10 w-14 rounded-2xl" />
            </div>
            <div className="skeleton h-20 rounded-2xl" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ProfilePage() {
  const router = useRouter();
  const { user, token, loading, refreshUser } = useAuth();

  const [ratings, setRatings] = useState<RatedProductDetail[]>([]);
  const [ratingsLoading, setRatingsLoading] = useState(true);

  const [editing, setEditing] = useState(false);
  const [skinType, setSkinType] = useState("");
  const [skinTone, setSkinTone] = useState("");
  const [undertone, setUndertone] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.replace("/");
  }, [loading, user, router]);

  useEffect(() => {
    if (!token) return;
    api
      .getMyInteractionsDetailed(token)
      .then(setRatings)
      .catch(() => {})
      .finally(() => setRatingsLoading(false));
  }, [token]);

  function startEdit() {
    if (!user) return;
    setSkinType(user.skin_type);
    setSkinTone(user.skin_tone);
    setUndertone(user.undertone);
    setSaveError("");
    setSaveSuccess(false);
    setEditing(true);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setSaving(true);
    setSaveError("");
    setSaveSuccess(false);
    try {
      await api.updateProfile(token, {
        skin_type: skinType,
        skin_tone: skinTone,
        undertone,
      });
      await refreshUser(token);
      setSaveSuccess(true);
      setEditing(false);
    } catch (err) {
      setSaveError(err instanceof ApiError ? err.message : "Kaydedilemedi.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center text-sm text-stone-400">
        Yükleniyor…
      </div>
    );
  }

  if (!user) return null;

  const ratedCount = ratings.length;
  const averageRating = ratedCount
    ? ratings.reduce((sum, item) => sum + item.rating, 0) / ratedCount
    : 0;
  const pricedProducts = ratings.filter((item) => item.price_usd != null).length;

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-8 px-5 py-8 md:px-6 md:py-10">
      <section className="animate-fade-up overflow-hidden rounded-[2rem] border border-[color:var(--border-strong)] bg-[linear-gradient(135deg,rgba(255,255,255,0.94),rgba(246,236,224,0.92))] shadow-[0_24px_60px_rgba(28,25,23,0.06)]">
        <div className="grid gap-8 px-6 py-8 md:grid-cols-[1.2fr_0.8fr] md:px-8 md:py-9">
          <div className="space-y-5">
            <div className="inline-flex w-fit items-center gap-2 rounded-full border border-white/80 bg-white/75 px-3 py-1 text-[11px] uppercase tracking-[0.22em] text-stone-500 shadow-sm">
              <span className="h-2 w-2 rounded-full bg-[var(--accent)]" />
              Profil merkezi
            </div>

            <div className="space-y-3">
              <h1 className="text-3xl font-light leading-tight text-stone-900 md:text-5xl">
                Tercihlerini yönet,
                <span className="block text-[color:var(--accent-deep)]">
                  öneri motorunu daha akıllı hale getir
                </span>
              </h1>
              <p className="max-w-2xl text-sm leading-7 text-stone-600">
                Burada cilt profilini güncelleyebilir, daha önce puanladığın ürünleri
                gözden geçirebilir ve kişiselleştirme derinliğini takip edebilirsin.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
                <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                  Hesap
                </p>
                <p className="mt-2 truncate text-sm font-medium text-stone-800">
                  {user.email}
                </p>
              </div>
              <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
                <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                  Puanlanan ürün
                </p>
                <p className="mt-2 text-2xl font-light text-stone-900">
                  {ratedCount}
                </p>
              </div>
              <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
                <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                  Ortalama puan
                </p>
                <p className="mt-2 text-2xl font-light text-stone-900">
                  {ratedCount ? averageRating.toFixed(1) : "--"}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-[1.75rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)]/92 p-5 shadow-[0_18px_50px_rgba(28,25,23,0.08)]">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-stone-400">
                  Hızlı özet
                </p>
                <p className="mt-1 text-sm text-stone-600">
                  Profil sinyallerin şu anda aktif
                </p>
              </div>
              {!editing && (
                <button
                  onClick={startEdit}
                  className="rounded-full border border-stone-200 bg-stone-50 px-3 py-1.5 text-xs text-stone-600 transition-colors hover:border-stone-400 hover:text-stone-900"
                >
                  Düzenle
                </button>
              )}
            </div>

            <div className="space-y-3">
              {[
                ["Cilt tipi", user.skin_type],
                ["Cilt tonu", user.skin_tone],
                ["Alt ton", user.undertone],
              ].map(([label, value]) => (
                <div
                  key={label}
                  className="flex items-center justify-between rounded-2xl border border-stone-200/80 bg-stone-50/80 px-4 py-3"
                >
                  <span className="text-xs uppercase tracking-[0.14em] text-stone-400">
                    {label}
                  </span>
                  <span className="text-sm font-medium text-stone-800">
                    {toTitleCase(value)}
                  </span>
                </div>
              ))}
            </div>

            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl bg-stone-50 p-4">
                <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                  Fiyat bilgili ürün
                </p>
                <p className="mt-2 text-lg font-light text-stone-900">
                  {pricedProducts}
                </p>
              </div>
              <div className="rounded-2xl bg-stone-50 p-4">
                <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                  Durum
                </p>
                <p className="mt-2 text-sm font-medium text-stone-800">
                  {ratedCount >= 3 ? "Kişiselleştirme güçlü" : "Başlangıç aşaması"}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="animate-fade-up-delay-1 rounded-[2rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-6 py-7 shadow-[0_20px_50px_rgba(28,25,23,0.05)] md:px-8">
        <div className="mb-6 flex items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-stone-400">
              Profil bilgileri
            </p>
            <p className="mt-2 text-sm leading-7 text-stone-500">
              Başlangıç önerilerini etkileyen temel alanlar burada tutulur.
            </p>
          </div>
          {!editing && (
            <button
              onClick={startEdit}
              className="rounded-full border border-stone-200 bg-stone-50 px-4 py-2 text-xs text-stone-600 transition-colors hover:border-stone-400 hover:text-stone-900"
            >
              Profili düzenle
            </button>
          )}
        </div>

        {!editing ? (
          <div className="grid gap-4 md:grid-cols-4">
            {[
              ["E-posta", user.email],
              ["Cilt tipi", toTitleCase(user.skin_type)],
              ["Cilt tonu", toTitleCase(user.skin_tone)],
              ["Alt ton", toTitleCase(user.undertone)],
            ].map(([label, value]) => (
              <div
                key={label}
                className="rounded-[1.5rem] border border-stone-200 bg-stone-50/70 p-5"
              >
                <span className="block text-xs uppercase tracking-[0.12em] text-stone-400">
                  {label}
                </span>
                <span className="mt-2 block text-sm font-medium text-stone-800">
                  {value}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <form onSubmit={handleSave} className="flex flex-col gap-5">
            <div className="grid gap-4 md:grid-cols-3">
              <div className="flex flex-col gap-2">
                <label className="text-xs uppercase tracking-[0.15em] text-stone-500">
                  Cilt tipi
                </label>
                <select
                  value={skinType}
                  onChange={(e) => setSkinType(e.target.value)}
                  required
                  className="rounded-2xl border border-stone-200 bg-stone-50/80 px-4 py-3 text-sm text-stone-800 outline-none transition-colors focus:border-stone-700"
                >
                  {SKIN_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-xs uppercase tracking-[0.15em] text-stone-500">
                  Cilt tonu
                </label>
                <select
                  value={skinTone}
                  onChange={(e) => setSkinTone(e.target.value)}
                  required
                  className="rounded-2xl border border-stone-200 bg-stone-50/80 px-4 py-3 text-sm text-stone-800 outline-none transition-colors focus:border-stone-700"
                >
                  {SKIN_TONES.map((tone) => (
                    <option key={tone.value} value={tone.value}>
                      {tone.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-xs uppercase tracking-[0.15em] text-stone-500">
                  Alt ton
                </label>
                <select
                  value={undertone}
                  onChange={(e) => setUndertone(e.target.value)}
                  required
                  className="rounded-2xl border border-stone-200 bg-stone-50/80 px-4 py-3 text-sm text-stone-800 outline-none transition-colors focus:border-stone-700"
                >
                  {UNDERTONES.map((tone) => (
                    <option key={tone.value} value={tone.value}>
                      {tone.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {saveError && (
              <p className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                {saveError}
              </p>
            )}

            <div className="flex flex-wrap gap-3">
              <button
                type="submit"
                disabled={saving}
                className="rounded-2xl bg-stone-900 px-6 py-3 text-xs uppercase tracking-[0.2em] text-white transition-all hover:-translate-y-0.5 hover:bg-stone-700 disabled:opacity-40"
              >
                {saving ? "Kaydediliyor…" : "Kaydet"}
              </button>
              <button
                type="button"
                onClick={() => setEditing(false)}
                className="rounded-2xl border border-stone-200 bg-white px-5 py-3 text-xs uppercase tracking-[0.18em] text-stone-600 transition-colors hover:border-stone-400 hover:text-stone-900"
              >
                İptal
              </button>
            </div>
          </form>
        )}

        {saveSuccess && (
          <p className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            Profil güncellendi.
          </p>
        )}
      </section>

      <section className="animate-fade-up-delay-2 rounded-[2rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-6 py-7 shadow-[0_20px_50px_rgba(28,25,23,0.05)] md:px-8">
        <div className="mb-6 flex items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-stone-400">
              Puanlanan ürünler
            </p>
            <p className="mt-2 text-sm leading-7 text-stone-500">
              Davranış tabanlı kişiselleştirme bu geçmişten öğreniyor.
            </p>
          </div>
          <span className="rounded-full border border-stone-200 bg-stone-50 px-3 py-1.5 text-xs text-stone-500">
            {ratedCount} ürün
          </span>
        </div>

        {ratingsLoading ? (
          <ProfileRatingsSkeleton />
        ) : ratedCount === 0 ? (
          <div className="rounded-[1.75rem] border border-dashed border-stone-300 bg-stone-50/60 p-10 text-center">
            <div className="animate-soft-float mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[linear-gradient(135deg,rgba(198,137,66,0.14),rgba(140,91,36,0.2))] text-2xl text-[color:var(--accent-deep)]">
              ☆
            </div>
            <p className="text-sm text-stone-500">Henüz hiç ürün puanlamadın.</p>
            <p className="mt-2 text-xs text-stone-400">
              Keşfet sayfasından ürünleri puanlayarak önerileri güçlendirebilirsin.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {ratings.map((item) => (
              <div
                key={item.product_id}
                className="flex flex-col gap-4 rounded-[1.75rem] border border-stone-200 bg-stone-50/50 p-5"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                      {item.tertiary_category}
                    </p>
                    <h3 className="mt-2 text-sm font-medium leading-snug text-stone-900">
                      {item.product_name}
                    </h3>
                    <p className="mt-1 text-xs text-stone-500">{item.brand_name}</p>
                  </div>
                  {item.price_usd != null && (
                    <div className="rounded-2xl bg-white px-3 py-2 text-xs font-medium text-stone-700 shadow-sm">
                      ${item.price_usd.toFixed(0)}
                    </div>
                  )}
                </div>

                <div className="rounded-2xl border border-stone-200 bg-white/80 p-4">
                  <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                    Verdiğin puan
                  </p>
                  <div className="mt-2 flex items-center gap-1">
                    {STARS.map((star) => (
                      <span
                        key={star}
                        className={`text-base leading-none ${
                          star <= item.rating ? "text-amber-500" : "text-stone-200"
                        }`}
                      >
                        ★
                      </span>
                    ))}
                    <span className="ml-2 text-xs text-stone-500">{item.rating}/5</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
