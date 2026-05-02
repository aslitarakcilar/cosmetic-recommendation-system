"use client";

import { useEffect, useState } from "react";
import type { RecommendationItem } from "../lib/api";

interface Props {
  item: RecommendationItem;
  rank: number;
  initialRating?: number;
  onRate?: (product_id: string, rating: number) => Promise<void>;
}

function buildReason(item: RecommendationItem) {
  if (item.score != null && item.score >= 0.8) {
    return "Yuksek uyum skoru ile one cikiyor.";
  }
  if (item.rating != null && item.rating >= 4.3) {
    return "Genel kullanici puani guclu oldugu icin oneriliyor.";
  }
  if (item.secondary_category) {
    return `${item.secondary_category} grubunda benzer ihtiyaca hitap ediyor.`;
  }
  return "Kategori ve profil sinyallerine gore uygun bir eslesme.";
}

function getMatchSummary(score: number | null) {
  if (score == null || !Number.isFinite(score)) {
    return {
      label: "Degerlendiriliyor",
      tone: "text-stone-700",
      helper: "Model bu urunu ilgili kategori icinde uygun buldu.",
    };
  }

  if (score >= 0.75) {
    return {
      label: "Cok yuksek uyum",
      tone: "text-emerald-700",
      helper: "Bu urun senin profilin ve sinyallerinle guclu eslesiyor.",
    };
  }

  if (score >= 0.2) {
    return {
      label: "Yuksek uyum",
      tone: "text-emerald-700",
      helper: "Model bu urunu ust siralarda gostermeye deger buldu.",
    };
  }

  if (score >= -0.6) {
    return {
      label: "Iyi uyum",
      tone: "text-amber-700",
      helper: "Kategori icinde anlamli bir aday olarak onde yer aliyor.",
    };
  }

  if (score >= -1.6) {
    return {
      label: "Uygun aday",
      tone: "text-amber-700",
      helper: "Liste icinde destekleyici bir secenek olarak oneriliyor.",
    };
  }

  return {
    label: "Kesfedilebilir",
    tone: "text-stone-700",
    helper: "Daha niş ama yine de kategori baglaminda ilgili bir secenek.",
  };
}

export function ProductCard({ item, rank, initialRating, onRate }: Props) {
  const [myRating, setMyRating] = useState<number | null>(initialRating ?? null);
  const [hovered, setHovered] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setMyRating(initialRating ?? null);
  }, [initialRating]);

  async function handleRate(stars: number) {
    if (!onRate || saving) return;
    setSaving(true);
    try {
      await onRate(item.product_id, stars);
      setMyRating(stars);
    } finally {
      setSaving(false);
    }
  }

  const priceLabel =
    item.price_usd != null ? `$${item.price_usd.toFixed(0)}` : "Fiyat yok";
  const recommendationReason = buildReason(item);
  const matchSummary = getMatchSummary(item.score);

  return (
    <article className="group flex h-full flex-col overflow-hidden rounded-[1.75rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] shadow-[0_14px_32px_rgba(28,25,23,0.05)] transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_18px_42px_rgba(28,25,23,0.1)]">
      <div className="relative overflow-hidden border-b border-stone-200/80 bg-[radial-gradient(circle_at_top_left,rgba(212,168,104,0.28),transparent_55%),linear-gradient(135deg,#f9f4ed,#f3ece3)] px-5 pb-5 pt-4">
        <div className="absolute right-3 top-3 rounded-full border border-white/70 bg-white/80 px-2.5 py-1 text-[11px] font-medium text-stone-600 shadow-sm">
          #{String(rank).padStart(2, "0")}
        </div>

        <div className="mt-8 flex items-start justify-between gap-3">
          <div>
            <p className="text-[11px] uppercase tracking-[0.2em] text-stone-500">
              {item.primary_category}
            </p>
            <h3 className="mt-2 text-base font-medium leading-snug text-stone-900">
              {item.product_name}
            </h3>
            <p className="mt-1 text-xs uppercase tracking-[0.15em] text-stone-500">
              {item.brand_name}
            </p>
          </div>

          {item.rating !== null && item.rating !== undefined && (
            <div className="rounded-2xl bg-white/85 px-3 py-2 text-right shadow-sm">
              <p className="text-[11px] uppercase tracking-[0.15em] text-stone-400">
                Puan
              </p>
              <p className="mt-1 text-sm font-medium text-amber-700">
                ★ {item.rating.toFixed(1)}
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-4 px-5 py-5">
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full bg-stone-100 px-3 py-1 text-[11px] text-stone-600">
            {item.secondary_category}
          </span>
          <span className="rounded-full bg-stone-100 px-3 py-1 text-[11px] text-stone-600">
            {item.tertiary_category}
          </span>
        </div>

        <div className="rounded-2xl border border-stone-200 bg-stone-50/80 p-4">
          <p className="text-[11px] uppercase tracking-[0.18em] text-stone-400">
            Neden onerildi?
          </p>
          <p className="mt-2 text-sm leading-6 text-stone-600">
            {recommendationReason}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-2xl bg-stone-50 p-3">
            <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
              Fiyat
            </p>
            <p className="mt-1 text-sm font-medium text-stone-800">
              {priceLabel}
            </p>
          </div>
          <div className="rounded-2xl bg-stone-50 p-3">
            <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
              Uyum
            </p>
            <p className={`mt-1 text-sm font-medium ${matchSummary.tone}`}>
              {matchSummary.label}
            </p>
            <p className="mt-1 text-[11px] leading-5 text-stone-400">
              {matchSummary.helper}
            </p>
          </div>
        </div>

        {onRate && (
          <div className="mt-auto border-t border-stone-100 pt-4">
            <div className="mb-2 flex items-center justify-between gap-3">
              <span className="text-xs text-stone-500">
                {myRating ? `Senin puanin: ${myRating}/5` : "Bu urunu puanla"}
              </span>
              {saving && (
                <span className="text-[11px] uppercase tracking-[0.14em] text-amber-700">
                  Kaydediliyor
                </span>
              )}
            </div>
            <div className="flex gap-1" onMouseLeave={() => setHovered(null)}>
              {[1, 2, 3, 4, 5].map((star) => {
                const filled = (hovered ?? myRating ?? 0) >= star;
                return (
                  <button
                    key={star}
                    type="button"
                    onClick={() => handleRate(star)}
                    onMouseEnter={() => setHovered(star)}
                    disabled={saving}
                    className={`rounded-full px-1 text-xl leading-none transition-colors disabled:cursor-not-allowed ${
                      filled ? "text-amber-500" : "text-stone-200 hover:text-amber-300"
                    }`}
                    aria-label={`${star} yildiz ver`}
                  >
                    ★
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </article>
  );
}
