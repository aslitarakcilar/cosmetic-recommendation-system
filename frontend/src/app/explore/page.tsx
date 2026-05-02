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

const MIN_FOR_PERSONALIZATION = 3;

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

  // Kullanıcının puanlamalarını takip et
  const [myRatings, setMyRatings] = useState<Record<string, number>>({});
  const ratingsLoaded = useRef(false);

  // Auth guard
  useEffect(() => {
    if (!loading && !user) router.replace("/");
  }, [loading, user, router]);

  // Kategori listesini yükle
  useEffect(() => {
    api
      .getCategories()
      .then((d) => setCategories(d.categories))
      .catch(() => setError("Kategoriler yüklenemedi."))
      .finally(() => setCatLoading(false));
  }, []);

  // Mevcut puanlamaları yükle
  useEffect(() => {
    if (!token || ratingsLoaded.current) return;
    ratingsLoaded.current = true;
    api
      .getMyInteractions(token)
      .then((list: RateResponse[]) => {
        const map: Record<string, number> = {};
        list.forEach((i) => { map[i.product_id] = i.rating; });
        setMyRatings(map);
      })
      .catch(() => { /* sessizce geç */ });
  }, [token]);

  const handleRate = useCallback(
    async (product_id: string, rating: number) => {
      if (!token) return;
      await api.rateProduct(token, product_id, rating);
      setMyRatings((prev) => ({ ...prev, [product_id]: rating }));
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
      <div className="flex items-center justify-center min-h-[calc(100vh-3.5rem)] text-stone-400 text-sm">
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

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      {/* ── Profil özeti ────────────────────────────────── */}
      <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-5">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-stone-400 mb-1">
            Hoş geldin
          </p>
          <p className="text-sm text-stone-600 truncate max-w-xs">{user.email}</p>
        </div>

        <div className="flex flex-wrap gap-3">
          {[
            ["Cilt tipi", user.skin_type],
            ["Cilt tonu", user.skin_tone],
            ["Alt ton", user.undertone],
          ].map(([label, value]) => (
            <div
              key={label}
              className="border border-stone-200 bg-white px-3 py-2 text-xs"
            >
              <span className="block uppercase tracking-[0.1em] text-stone-400">
                {label}
              </span>
              <span className="font-medium text-stone-700 capitalize">
                {value}
              </span>
            </div>
          ))}
          <div className="border border-stone-200 bg-white px-3 py-2 text-xs">
            <span className="block uppercase tracking-[0.1em] text-stone-400">
              Puanlamalar
            </span>
            <span className="font-medium text-stone-700">{ratingCount}</span>
          </div>
        </div>
      </div>

      {/* ── Kişiselleştirme ilerleme notu ────────────────── */}
      {ratingCount < MIN_FOR_PERSONALIZATION && (
        <div className="mb-6 border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800 flex items-center gap-2">
          <span>
            İçerik tabanlı kişiselleştirme için{" "}
            <strong>{remainingForPersonalization} ürün daha</strong> puanla.
            Şu an cilt profilin kullanılıyor.
          </span>
          <div className="ml-auto flex gap-0.5">
            {Array.from({ length: MIN_FOR_PERSONALIZATION }).map((_, i) => (
              <span
                key={i}
                className={`w-4 h-1.5 rounded-full ${
                  i < ratingCount ? "bg-amber-500" : "bg-amber-200"
                }`}
              />
            ))}
          </div>
        </div>
      )}

      {ratingCount >= MIN_FOR_PERSONALIZATION && (
        <div className="mb-6 border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs text-emerald-800">
          ✓ Yeterli puanlaman var. İçerik tabanlı kişiselleştirme aktif.
        </div>
      )}

      {/* ── Arama formu ─────────────────────────────────── */}
      <form
        onSubmit={handleRecommend}
        className="bg-white border border-stone-200 p-5 flex flex-wrap gap-5 items-end mb-8"
      >
        <div className="flex flex-col gap-1 flex-1 min-w-[200px]">
          <label className="text-xs uppercase tracking-[0.15em] text-stone-500">
            Kategori
          </label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            disabled={catLoading}
            required
            className="border-b border-stone-300 bg-transparent py-2.5 text-sm text-stone-800 outline-none focus:border-stone-700 transition-colors"
          >
            <option value="">
              {catLoading ? "Yükleniyor…" : "Kategori seçiniz"}
            </option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs uppercase tracking-[0.15em] text-stone-500">
            Adet
          </label>
          <select
            value={topN}
            onChange={(e) => setTopN(Number(e.target.value))}
            className="border-b border-stone-300 bg-transparent py-2.5 text-sm text-stone-800 outline-none focus:border-stone-700 transition-colors"
          >
            {[5, 10, 20].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          disabled={fetching || catLoading || !category}
          className="bg-stone-900 text-white px-8 py-2.5 text-sm uppercase tracking-widest hover:bg-stone-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {fetching ? "Yükleniyor…" : "Öner"}
        </button>
      </form>

      {/* ── Hata ──────────────────────────────────────────── */}
      {error && (
        <div className="mb-6 text-sm text-red-600 bg-red-50 border border-red-200 px-4 py-3">
          {error}
        </div>
      )}

      {/* ── Sonuçlar ──────────────────────────────────────── */}
      {result && (
        <div className="flex flex-col gap-5">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
            <ModelBadge
              model={result.model_used}
              explanation={result.model_explanation}
            />
            <span className="text-xs text-stone-400">
              {result.total_recommendations} ürün
            </span>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-px bg-stone-200">
            {result.recommendations.map((item, i) => (
              <ProductCard
                key={item.product_id}
                item={item}
                rank={i + 1}
                initialRating={myRatings[item.product_id]}
                onRate={handleRate}
              />
            ))}
          </div>
        </div>
      )}

      {/* ── Boş durum ─────────────────────────────────────── */}
      {!result && !fetching && !error && (
        <div className="border border-dashed border-stone-300 p-14 text-center">
          <p className="text-stone-400 text-sm">
            Kategori seçerek kişiselleştirilmiş önerileri görün.
          </p>
        </div>
      )}
    </div>
  );
}
