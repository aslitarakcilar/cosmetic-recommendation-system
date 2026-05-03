"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ModelBadge } from "../../components/ModelBadge";
import { ProductCard } from "../../components/ProductCard";
import { useAuth } from "../../contexts/AuthContext";
import {
  api,
  ApiError,
  type RateResponse,
  type RecommendResponse,
} from "../../lib/api";
import { toTitleCase } from "../../lib/utils";

const MIN_FOR_PERSONALIZATION = 3;
const TOP_N_OPTIONS = [5, 10, 20];

const MODEL_SUMMARY: Record<string, string> = {
  lightfm: "Davranış örüntülerine göre benzer kullanıcı tercihleri öne çıkarıldı.",
  hybrid: "Profil sinyalleri ile davranışsal sinyaller birlikte dengelendi.",
  content_seeded: "Puanladığın ürünlerin içerik ve metin benzerlikleri kullanıldı.",
  profile: "Cilt tipi, tonu ve alt ton bilgilerine göre eşleşmeler seçildi.",
  popularity: "Bu kategoride geniş kullanıcı kitlesince beğenilen ürünler öne alındı.",
  hybrid_fallback_popularity: "Kişiselleştirme sinyali yetmediği için kategori popülerliği devreye girdi.",
};

function RecommendationSkeleton() {
  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(270px,1fr))] gap-4">
      {Array.from({ length: 4 }).map((_, index) => (
        <div
          key={index}
          className="overflow-hidden rounded-[1.75rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] shadow-[0_14px_32px_rgba(28,25,23,0.05)]"
        >
          <div className="skeleton h-32 w-full" />
          <div className="space-y-4 p-5">
            <div className="skeleton h-4 w-1/3 rounded-full" />
            <div className="skeleton h-5 w-4/5 rounded-full" />
            <div className="skeleton h-4 w-2/3 rounded-full" />
            <div className="grid grid-cols-2 gap-3">
              <div className="skeleton h-16 rounded-2xl" />
              <div className="skeleton h-16 rounded-2xl" />
            </div>
            <div className="skeleton h-5 w-1/2 rounded-full" />
          </div>
        </div>
      ))}
    </div>
  );
}


export default function ExplorePage() {
  const router = useRouter();
  const { user, token, loading } = useAuth();

  const [categories, setCategories] = useState<string[]>([]);
  const [category, setCategory] = useState("");
  const [topN, setTopN] = useState(10);
  const [result, setResult] = useState<RecommendResponse | null>(null);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState("");
  const [catLoading, setCatLoading] = useState(true);

  const [myRatings, setMyRatings] = useState<Record<string, number>>({});
  const ratingsLoaded = useRef(false);

  useEffect(() => {
    if (!loading && !user) router.replace("/");
  }, [loading, user, router]);

  useEffect(() => {
    api
      .getCategories()
      .then((d) => setCategories(d.categories))
      .catch(() => setError("Kategoriler yüklenemedi."))
      .finally(() => setCatLoading(false));
  }, []);

  useEffect(() => {
    if (!token || ratingsLoaded.current) return;
    ratingsLoaded.current = true;
    api
      .getMyInteractions(token)
      .then((list: RateResponse[]) => {
        const map: Record<string, number> = {};
        list.forEach((interaction) => {
          map[interaction.product_id] = interaction.rating;
        });
        setMyRatings(map);
      })
      .catch(() => {});
  }, [token]);

  const handleRate = useCallback(
    async (product_id: string, rating: number, recommendationEventId?: number) => {
      if (!token) return;
      await api.rateProduct(token, product_id, rating, recommendationEventId);
      setMyRatings((prev) => ({ ...prev, [product_id]: rating }));
    },
    [token],
  );

  const handleInspect = useCallback(
    async (product_id: string, recommendationEventId?: number) => {
      if (!token || !recommendationEventId) return;
      await api.logRecommendationClick(token, recommendationEventId, product_id);
    },
    [token],
  );

  async function handleRecommend(e: React.FormEvent) {
    e.preventDefault();
    if (!category || !token) return;
    setFetching(true);
    setError("");
    setResult(null);

    try {
      const data = await api.getRecommendations(token, category, topN);
      setResult(data);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Öneriler alınamadı.",
      );
    } finally {
      setFetching(false);
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

  const ratingCount = Object.keys(myRatings).length;
  const remainingForPersonalization = Math.max(
    0,
    MIN_FOR_PERSONALIZATION - ratingCount,
  );
  const personalizationRatio = Math.min(
    100,
    Math.round((ratingCount / MIN_FOR_PERSONALIZATION) * 100),
  );
  const selectedModelSummary = result
    ? MODEL_SUMMARY[result.model_used] ?? MODEL_SUMMARY.popularity
    : "Henüz öneri alınmadı. Kategori seçtiğinde uygun model otomatik belirlenir.";

  const primaryCategoryCount = result
    ? new Set(result.recommendations.map((item) => item.secondary_category)).size
    : 0;
  const pricedCount = result
    ? result.recommendations.filter((item) => item.price_usd != null).length
    : 0;
  const ratedRecommendationCount = result
    ? result.recommendations.filter((item) => item.rating != null).length
    : 0;
  const averageProductRating = result
    ? result.recommendations.reduce((sum, item) => sum + (item.rating ?? 0), 0) /
      Math.max(ratedRecommendationCount, 1)
    : 0;

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-8 px-5 py-8 md:px-6 md:py-10">
      <section className="animate-fade-up overflow-hidden rounded-[2rem] border border-[color:var(--border-strong)] bg-[linear-gradient(135deg,rgba(255,255,255,0.96),rgba(248,241,232,0.92))] shadow-[0_30px_80px_rgba(28,25,23,0.07)]">
        <div className="grid gap-8 px-6 py-8 md:grid-cols-[1.3fr_0.9fr] md:px-8 md:py-9">
          <div className="space-y-5">
            <div className="inline-flex w-fit items-center gap-2 rounded-full border border-white/70 bg-white/75 px-3 py-1 text-[11px] uppercase tracking-[0.24em] text-stone-500 shadow-sm backdrop-blur">
              <span className="h-2 w-2 rounded-full bg-[var(--accent)]" />
              Kişiselleştirilmiş keşif alanı
            </div>

            <div className="space-y-3">
              <h1 className="max-w-2xl text-3xl font-light leading-tight text-stone-900 md:text-5xl">
                Profilin ve puanlamalarınla
                <span className="block text-[color:var(--accent-deep)]">
                  daha isabetli ürün önerileri
                </span>
              </h1>
              <p className="max-w-2xl text-sm leading-7 text-stone-600 md:text-[15px]">
                Sistem, kategori bazında senin profil sinyallerini ve davranış
                geçmişini birlikte değerlendirir. Ne kadar çok puanlama yaparsan
                sonuçlar o kadar kişisel hale gelir.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
                <p className="text-[11px] uppercase tracking-[0.18em] text-stone-400">
                  Kullanıcı
                </p>
                <p className="mt-2 truncate text-sm font-medium text-stone-800">
                  {user.email}
                </p>
              </div>
              <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
                <p className="text-[11px] uppercase tracking-[0.18em] text-stone-400">
                  Puanlama
                </p>
                <p className="mt-2 text-2xl font-light text-stone-900">
                  {ratingCount}
                </p>
              </div>
              <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
                <p className="text-[11px] uppercase tracking-[0.18em] text-stone-400">
                  Hazır kategori
                </p>
                <p className="mt-2 text-2xl font-light text-stone-900">
                  {catLoading ? "..." : categories.length}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-[1.75rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)]/92 p-5 shadow-[0_18px_50px_rgba(28,25,23,0.08)] backdrop-blur">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-stone-400">
                  Profil özeti
                </p>
                <p className="mt-1 text-sm text-stone-600">
                  Tavsiye motorunun ilk referans noktası
                </p>
              </div>
              <div className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-800">
                %{personalizationRatio}
              </div>
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
                  <span className="text-sm font-medium capitalize text-stone-800">
                    {toTitleCase(value)}
                  </span>
                </div>
              ))}
            </div>

            <div className="mt-5 space-y-2">
              <div className="flex items-center justify-between text-xs text-stone-500">
                <span>Kişiselleştirme eşiği</span>
                <span>{Math.min(ratingCount, MIN_FOR_PERSONALIZATION)}/{MIN_FOR_PERSONALIZATION}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-stone-200">
                <div
                  className="h-full rounded-full bg-[linear-gradient(90deg,var(--accent),var(--accent-deep))] transition-all duration-300"
                  style={{ width: `${personalizationRatio}%` }}
                />
              </div>
              <p className="text-xs leading-6 text-stone-500">
                {ratingCount < MIN_FOR_PERSONALIZATION
                  ? `${remainingForPersonalization} ürün daha puanladığında davranış tabanlı kişiselleştirme daha güçlü çalışır.`
                  : "Yeterli puanlama var. Sistem davranış verini daha güvenle kullanabilir."}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="animate-fade-up-delay-1 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <form
          onSubmit={handleRecommend}
          className="rounded-[1.75rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-5 py-5 shadow-[0_16px_40px_rgba(28,25,23,0.05)]"
        >
          <div className="mb-5 flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-stone-400">
                Öneri isteği
              </p>
              <h2 className="mt-1 text-xl font-light text-stone-900">
                Hangi kategoriyi keşfetmek istiyorsun?
              </h2>
            </div>
            <div className="rounded-full border border-stone-200 bg-stone-50 px-3 py-1 text-xs text-stone-500">
              {fetching ? "Hazırlanıyor" : "Hazır"}
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-[1fr_180px_auto] md:items-end">
            <div className="flex flex-col gap-2">
              <label className="text-xs uppercase tracking-[0.15em] text-stone-500">
                Kategori
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                disabled={catLoading}
                required
                className="rounded-2xl border border-stone-200 bg-stone-50/70 px-4 py-3 text-sm text-stone-800 outline-none transition-colors focus:border-stone-700"
              >
                <option value="">
                  {catLoading ? "Yükleniyor…" : "Kategori seçiniz"}
                </option>
                {categories.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs uppercase tracking-[0.15em] text-stone-500">
                Liste boyutu
              </label>
              <select
                value={topN}
                onChange={(e) => setTopN(Number(e.target.value))}
                className="rounded-2xl border border-stone-200 bg-stone-50/70 px-4 py-3 text-sm text-stone-800 outline-none transition-colors focus:border-stone-700"
              >
                {TOP_N_OPTIONS.map((count) => (
                  <option key={count} value={count}>
                    {count} ürün
                  </option>
                ))}
              </select>
            </div>

            <button
              type="submit"
              disabled={fetching || catLoading || !category}
              className="rounded-2xl bg-stone-900 px-6 py-3 text-sm uppercase tracking-[0.2em] text-white transition-all hover:-translate-y-0.5 hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {fetching ? "Hazırlanıyor…" : "Önerileri getir"}
            </button>
          </div>

          <div className="mt-5 flex flex-wrap gap-2">
            {categories.slice(0, 6).map((quickCategory) => (
              <button
                key={quickCategory}
                type="button"
                onClick={() => setCategory(quickCategory)}
                className={`rounded-full border px-3 py-1.5 text-xs transition-colors ${
                  category === quickCategory
                    ? "border-amber-300 bg-amber-50 text-amber-900"
                    : "border-stone-200 bg-white text-stone-500 hover:border-stone-300 hover:text-stone-800"
                }`}
              >
                {quickCategory}
              </button>
            ))}
          </div>
        </form>

        <div className="rounded-[1.75rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-5 py-5 shadow-[0_16px_40px_rgba(28,25,23,0.05)]">
          <p className="text-xs uppercase tracking-[0.18em] text-stone-400">
            Bu öneri nasıl kuruluyor?
          </p>
          <p className="mt-3 text-sm leading-7 text-stone-600">
            {selectedModelSummary}
          </p>
          <div className="mt-5 grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            <div className="rounded-2xl bg-stone-50 p-4">
              <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                Profil etkisi
              </p>
              <p className="mt-2 text-sm text-stone-700">
                {ratingCount < MIN_FOR_PERSONALIZATION
                  ? "Yüksek"
                  : "Dengelenmiş"}
              </p>
            </div>
            <div className="rounded-2xl bg-stone-50 p-4">
              <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                Davranış sinyali
              </p>
              <p className="mt-2 text-sm text-stone-700">
                {ratingCount} puanlama kaydı
              </p>
            </div>
            <div className="rounded-2xl bg-stone-50 p-4">
              <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                Seçili kategori
              </p>
              <p className="mt-2 text-sm text-stone-700">
                {category || "Henüz seçilmedi"}
              </p>
            </div>
          </div>
        </div>
      </section>

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {fetching && (
        <section className="animate-fade-up-delay-2 space-y-5">
          <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-[1.75rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-5 py-5 shadow-[0_16px_40px_rgba(28,25,23,0.05)]">
              <div className="space-y-3">
                <div className="skeleton h-4 w-28 rounded-full" />
                <div className="skeleton h-8 w-3/4 rounded-full" />
                <div className="skeleton h-4 w-full rounded-full" />
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              {Array.from({ length: 3 }).map((_, index) => (
                <div
                  key={index}
                  className="rounded-[1.5rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] p-4 shadow-[0_16px_40px_rgba(28,25,23,0.05)]"
                >
                  <div className="skeleton h-4 w-20 rounded-full" />
                  <div className="mt-3 skeleton h-10 w-16 rounded-full" />
                  <div className="mt-2 skeleton h-3 w-24 rounded-full" />
                </div>
              ))}
            </div>
          </div>
          <RecommendationSkeleton />
        </section>
      )}

      {result && !fetching && (
        <section className="animate-fade-up-delay-2 space-y-5">
          <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-[1.75rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-5 py-5 shadow-[0_16px_40px_rgba(28,25,23,0.05)]">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div className="space-y-3">
                  <p className="text-xs uppercase tracking-[0.18em] text-stone-400">
                    Sonuç özeti
                  </p>
                  <ModelBadge
                    model={result.model_used}
                    explanation={result.model_explanation}
                  />
                </div>
                <div className="rounded-2xl bg-stone-50 px-4 py-3 text-right">
                  <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                    Seçilen kategori
                  </p>
                  <p className="mt-1 text-sm font-medium text-stone-800">
                    {category}
                  </p>
                </div>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-[1.5rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] p-4 shadow-[0_16px_40px_rgba(28,25,23,0.05)]">
                <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                  Öneri sayısı
                </p>
                <p className="mt-2 text-3xl font-light text-stone-900">
                  {result.total_recommendations}
                </p>
              </div>
              <div className="rounded-[1.5rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] p-4 shadow-[0_16px_40px_rgba(28,25,23,0.05)]">
                <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                  Alt kategori
                </p>
                <p className="mt-2 text-3xl font-light text-stone-900">
                  {primaryCategoryCount}
                </p>
              </div>
              <div className="rounded-[1.5rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] p-4 shadow-[0_16px_40px_rgba(28,25,23,0.05)]">
                <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                  Ortalama ürün puanı
                </p>
                <p className="mt-2 text-3xl font-light text-stone-900">
                  {ratedRecommendationCount > 0 ? averageProductRating.toFixed(1) : "--"}
                </p>
                <p className="mt-1 text-xs text-stone-400">
                  {ratedRecommendationCount} üründe puan, {pricedCount} üründe fiyat bilgisi var
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-[repeat(auto-fit,minmax(270px,1fr))] gap-4">
            {result.recommendations.map((item, index) => (
              <ProductCard
                key={item.product_id}
                item={item}
                rank={index + 1}
                initialRating={myRatings[item.product_id]}
                onRate={(product_id, rating) =>
                  handleRate(product_id, rating, result.recommendation_event_id)
                }
                onInspect={(product_id) =>
                  handleInspect(product_id, result.recommendation_event_id)
                }
              />
            ))}
          </div>
        </section>
      )}

      {!result && !fetching && !error && (
        <section className="animate-fade-up-delay-2 rounded-[2rem] border border-dashed border-stone-300 bg-white/70 px-6 py-12 text-center shadow-[0_12px_30px_rgba(28,25,23,0.03)]">
          <div className="mx-auto max-w-2xl">
            <div className="animate-soft-float mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[linear-gradient(135deg,rgba(198,137,66,0.14),rgba(140,91,36,0.2))] text-2xl text-[color:var(--accent-deep)]">
              ✦
            </div>
            <p className="text-xs uppercase tracking-[0.2em] text-stone-400">
              Keşif bekliyor
            </p>
            <h2 className="mt-3 text-2xl font-light text-stone-900">
              Bir kategori seç, sistem sana uygun ürünleri sıralasın
            </h2>
            <p className="mt-3 text-sm leading-7 text-stone-500">
              İlk öneriler profilini baz alır. Puanlama yaptıkça içerik ve
              davranış sinyalleri de devreye girer; böylece öneriler daha kişisel
              ve daha ikna edici hale gelir.
            </p>
          </div>
        </section>
      )}
    </div>
  );
}
