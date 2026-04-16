"use client";

import { useEffect, useState } from "react";

type RecommendationItem = {
  product_id: string;
  product_name: string;
  brand_name: string;
  primary_category: string;
  tertiary_category: string;
  price_usd?: number | null;
  score?: number | null;
};

export default function Home() {
  const [userId, setUserId] = useState("");
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [results, setResults] = useState<RecommendationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [error, setError] = useState("");
  const [modelUsed, setModelUsed] = useState("");

  // --------------------------------------------------------------
  // Sayfa açılınca backend'den kategori listesini çek
  // --------------------------------------------------------------
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/categories");

        if (!res.ok) {
          throw new Error("Kategori listesi alınamadı.");
        }

        const data = await res.json();
        setCategories(data.categories || []);
      } catch (err) {
        console.error(err);
        setError("Kategori listesi yüklenemedi.");
      } finally {
        setCategoriesLoading(false);
      }
    };

    fetchCategories();
  }, []);

  // --------------------------------------------------------------
  // Öneri isteği gönder
  // --------------------------------------------------------------
  const handleRecommend = async () => {
    if (!category) {
      setError("Please select a category.");
      return;
    }

    setLoading(true);
    setError("");
    setResults([]);
    setModelUsed("");

    try {
      const res = await fetch("http://127.0.0.1:8000/recommend", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId || null,
          category,
          top_n: 10,
        }),
      });

      if (!res.ok) {
        throw new Error("Öneriler alınamadı.");
      }

      const data = await res.json();
      setResults(data.recommendations || []);
      setModelUsed(data.model_used || "");
    } catch (err) {
      console.error(err);
      setError("Bir hata oluştu. Lütfen tekrar dene.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#f8f6f3] text-black font-serif">
      {/* HEADER */}
      <div className="flex items-center justify-between px-8 py-10">
        <h1 className="text-xl uppercase tracking-[0.3em]">
          Cosmetic Intelligence
        </h1>
      </div>

      {/* HERO */}
      <div className="max-w-3xl px-8 py-16">
        <h2 className="text-5xl font-light leading-tight">
          Discover what suits you
        </h2>

        <p className="mt-6 max-w-md text-neutral-600">
          A personalized recommendation system designed to match your aesthetic,
          your skin, and your preferences.
        </p>

        {/* FORM */}
        <div className="mt-12 space-y-4">
          <input
            placeholder="User ID"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            className="w-full border-b border-black bg-transparent py-3 outline-none"
          />

          <div>
            <label className="mb-2 block text-xs uppercase tracking-[0.25em] text-neutral-500">
              Category
            </label>

            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full border-b border-black bg-transparent py-3 outline-none"
              disabled={categoriesLoading}
            >
              <option value="">
                {categoriesLoading ? "Loading categories..." : "Select a category"}
              </option>

              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleRecommend}
            disabled={loading || categoriesLoading}
            className="mt-6 border border-black px-8 py-3 text-sm uppercase tracking-widest transition hover:bg-black hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Loading..." : "Get Recommendations"}
          </button>

          {modelUsed && (
            <p className="pt-2 text-xs uppercase tracking-[0.25em] text-neutral-500">
              model used: {modelUsed}
            </p>
          )}

          {error && (
            <p className="pt-2 text-sm text-red-600">
              {error}
            </p>
          )}
        </div>
      </div>

      {/* RESULTS */}
      <div className="px-8 pb-20">
        {results.length > 0 ? (
          <div className="grid gap-8 md:grid-cols-3">
            {results.map((item) => (
              <div
                key={item.product_id}
                className="border border-black p-6 transition hover:bg-black hover:text-white"
              >
                <h3 className="text-lg font-medium leading-snug">
                  {item.product_name}
                </h3>

                <p className="mt-2 text-sm opacity-70">
                  {item.brand_name}
                </p>

                <p className="mt-4 text-xs uppercase tracking-widest opacity-60">
                  {item.primary_category} / {item.tertiary_category}
                </p>

                {item.price_usd !== null && item.price_usd !== undefined && (
                  <p className="mt-4 text-sm">
                    ${item.price_usd}
                  </p>
                )}

                {item.score !== null && item.score !== undefined && (
                  <p className="mt-2 text-xs opacity-50">
                    score {item.score.toFixed(2)}
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : (
          !loading && (
            <div className="border border-black/20 p-8 text-sm text-neutral-500">
              No recommendations yet. Select a category and request recommendations.
            </div>
          )
        )}
      </div>
    </main>
  );
}