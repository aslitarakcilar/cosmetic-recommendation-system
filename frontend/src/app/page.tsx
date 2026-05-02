"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  // Giriş yapılmışsa direkt keşfet sayfasına yönlendir
  useEffect(() => {
    if (!loading && user) {
      router.replace("/explore");
    }
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-3.5rem)] text-stone-400 text-sm">
        Yükleniyor…
      </div>
    );
  }

  if (user) return null;

  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex flex-col md:flex-row">
      {/* ── Sol: Başlık + açıklama ────────────────────────── */}
      <div className="flex-1 flex flex-col justify-center px-10 md:px-16 py-16 max-w-xl">
        <p className="text-xs uppercase tracking-[0.25em] text-amber-700 mb-5">
          Bilgisayar Mühendisliği Tez Projesi
        </p>
        <h1 className="text-4xl md:text-5xl font-light text-stone-900 leading-snug">
          Kişiselleştirilmiş
          <br />
          <span className="italic text-amber-800">kozmetik önerisi</span>
        </h1>
        <p className="mt-5 text-stone-500 leading-relaxed text-sm max-w-sm">
          8.494 ürün ve 1 milyondan fazla Sephora yorumu üzerine kurulu öneri
          sistemi. Profil tabanlı, içerik tabanlı, collaborative filtering ve
          hybrid modeller karşılaştırılır.
        </p>

        <div className="mt-8 flex flex-col gap-2 text-xs text-stone-400">
          {[
            ["Popülerlik", "Kategori bazlı ağırlıklı ortalama"],
            ["Profil tabanlı", "Cilt tipi + ton eşleşmesi"],
            ["İçerik tabanlı", "TF-IDF metin benzerliği"],
            ["Collaborative Filtering", "SVD matris ayrıştırması"],
            ["Hybrid (CF + İçerik)", "Dinamik ağırlıklı birleşim"],
          ].map(([name, desc]) => (
            <div key={name} className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
              <span className="font-medium text-stone-600">{name}</span>
              <span className="text-stone-400">— {desc}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Sağ: Auth kartı ──────────────────────────────── */}
      <div className="flex items-center justify-center px-10 md:px-16 py-16 bg-stone-50 border-l border-stone-100 min-w-[320px]">
        <div className="w-full max-w-sm flex flex-col gap-4">
          <h2 className="text-lg font-light text-stone-800 mb-2">
            Başlamak için hesabına giriş yap
          </h2>

          <Link
            href="/register"
            className="w-full bg-stone-900 text-white text-center py-3 text-sm uppercase tracking-widest hover:bg-stone-700 transition-colors"
          >
            Kayıt ol
          </Link>

          <Link
            href="/login"
            className="w-full border border-stone-300 text-stone-700 text-center py-3 text-sm uppercase tracking-widest hover:border-stone-600 transition-colors"
          >
            Giriş yap
          </Link>

          <p className="text-xs text-stone-400 text-center pt-2 leading-relaxed">
            Cilt profiline göre sana uygun ürünler görmek için kayıt ol.
            Ürünleri puanladıkça öneriler kişiselleşir.
          </p>
        </div>
      </div>
    </div>
  );
}
