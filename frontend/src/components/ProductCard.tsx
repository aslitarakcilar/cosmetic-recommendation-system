"use client";

import { useState } from "react";
import type { RecommendationItem } from "../lib/api";

interface Props {
  item: RecommendationItem;
  rank: number;
  initialRating?: number;
  onRate?: (product_id: string, rating: number) => Promise<void>;
}

export function ProductCard({ item, rank, initialRating, onRate }: Props) {
  const [myRating, setMyRating] = useState<number | null>(initialRating ?? null);
  const [hovered, setHovered] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);

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

  return (
    <article className="bg-white border border-stone-200 p-5 flex flex-col gap-3 hover:border-stone-300 hover:shadow-sm transition-all duration-150">
      {/* Sıra + ürün puanı */}
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs font-mono text-stone-300 select-none">
          {String(rank).padStart(2, "0")}
        </span>
        {item.rating !== null && item.rating !== undefined && (
          <span className="text-xs text-amber-600 font-medium">
            ★ {item.rating.toFixed(1)}
          </span>
        )}
      </div>

      {/* Ürün bilgisi */}
      <div className="flex-1">
        <h3 className="text-sm font-medium text-stone-900 leading-snug">
          {item.product_name}
        </h3>
        <p className="mt-1 text-xs text-stone-500 uppercase tracking-wide">
          {item.brand_name}
        </p>
      </div>

      {/* Alt bilgi */}
      <div className="flex items-end justify-between pt-1 border-t border-stone-100">
        <span className="text-xs text-stone-400">{item.tertiary_category}</span>
        {item.price_usd != null ? (
          <span className="text-sm font-medium text-stone-700">
            ${item.price_usd.toFixed(0)}
          </span>
        ) : (
          <span className="text-xs text-stone-300">—</span>
        )}
      </div>

      {/* Puanlama — sadece onRate prop'u varsa göster */}
      {onRate && (
        <div className="pt-2 border-t border-stone-100 flex flex-col gap-1">
          <span className="text-xs text-stone-400">
            {myRating ? `Puanladın: ${myRating}/5` : "Puanla"}
          </span>
          <div
            className="flex gap-1"
            onMouseLeave={() => setHovered(null)}
          >
            {[1, 2, 3, 4, 5].map((star) => {
              const filled = (hovered ?? myRating ?? 0) >= star;
              return (
                <button
                  key={star}
                  onClick={() => handleRate(star)}
                  onMouseEnter={() => setHovered(star)}
                  disabled={saving}
                  className={`text-lg leading-none transition-colors disabled:cursor-not-allowed ${
                    filled ? "text-amber-400" : "text-stone-200 hover:text-amber-300"
                  }`}
                  aria-label={`${star} yıldız ver`}
                >
                  ★
                </button>
              );
            })}
          </div>
        </div>
      )}
    </article>
  );
}
