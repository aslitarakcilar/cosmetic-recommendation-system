"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";

const MODEL_ITEMS = [
  ["Popülerlik", "Kategori bazlı ağırlıklı ortalama ile güvenli başlangıç"],
  ["Profil tabanlı", "Cilt tipi, tonu ve alt ton sinyalleriyle ilk eşleşme"],
  ["İçerik tabanlı", "TF-IDF benzerliği ile sevilen ürünlere yakın öneriler"],
  ["Collaborative Filtering", "Benzer kullanıcı davranışlarından öğrenen model"],
  ["Hybrid", "Birden fazla yaklaşımı dinamik olarak dengeleyen karar katmanı"],
];

export default function HomePage() {
  const { user, loading, isAdmin } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.replace(isAdmin ? "/dashboard" : "/explore");
    }
  }, [loading, user, router, isAdmin]);

  if (loading) {
    return (
      <div className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center text-sm text-stone-400">
        Yükleniyor…
      </div>
    );
  }

  if (user) return null;

  return (
    <div className="mx-auto flex min-h-[calc(100vh-3.5rem)] max-w-7xl flex-col gap-8 px-5 py-8 md:px-6 md:py-10">
      <section className="overflow-hidden rounded-[2rem] border border-[color:var(--border-strong)] bg-[linear-gradient(135deg,rgba(255,255,255,0.94),rgba(246,236,224,0.92))] shadow-[0_30px_80px_rgba(28,25,23,0.07)]">
        <div className="grid gap-8 px-6 py-8 md:grid-cols-[1.15fr_0.85fr] md:px-8 md:py-10">
          <div className="space-y-6">
            <div className="inline-flex w-fit items-center gap-2 rounded-full border border-white/80 bg-white/75 px-3 py-1 text-[11px] uppercase tracking-[0.24em] text-stone-500 shadow-sm">
              <span className="h-2 w-2 rounded-full bg-[var(--accent)]" />
              Bilgisayar Mühendisliği Tez Projesi
            </div>

            <div className="space-y-4">
              <h1 className="max-w-3xl text-4xl font-light leading-tight text-stone-900 md:text-6xl">
                Sephora verisiyle eğitilmiş
                <span className="block text-[color:var(--accent-deep)]">
                  kişiselleştirilmiş kozmetik öneri sistemi
                </span>
              </h1>
              <p className="max-w-2xl text-sm leading-7 text-stone-600 md:text-[15px]">
                8.494 ürün ve 1 milyondan fazla yorum sinyalini kullanan bu sistem,
                yeni kullanıcıdan hibrit kişiselleştirmeye kadar farklı öneri
                stratejilerini tek bir deneyimde birleştiriyor.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
                <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                  Ürün
                </p>
                <p className="mt-2 text-2xl font-light text-stone-900">8.494</p>
                <p className="mt-1 text-xs text-stone-500">Sephora kataloğu</p>
              </div>
              <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
                <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                  Yorum
                </p>
                <p className="mt-2 text-2xl font-light text-stone-900">1M+</p>
                <p className="mt-1 text-xs text-stone-500">kullanıcı sinyali</p>
              </div>
              <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
                <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                  Yaklaşım
                </p>
                <p className="mt-2 text-2xl font-light text-stone-900">5</p>
                <p className="mt-1 text-xs text-stone-500">öneri stratejisi</p>
              </div>
            </div>

            <div className="flex flex-wrap gap-3 pt-2">
              <Link
                href="/register"
                className="rounded-full bg-stone-900 px-6 py-3 text-sm uppercase tracking-[0.2em] text-white transition-all hover:-translate-y-0.5 hover:bg-stone-700"
              >
                Hesap oluştur
              </Link>
              <Link
                href="/login"
                className="rounded-full border border-stone-300 bg-white/80 px-6 py-3 text-sm uppercase tracking-[0.2em] text-stone-700 transition-colors hover:border-stone-500 hover:text-stone-900"
              >
                Giriş yap
              </Link>
            </div>
          </div>

          <div className="rounded-[1.75rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)]/92 p-5 shadow-[0_18px_50px_rgba(28,25,23,0.08)]">
            <div className="mb-5">
              <p className="text-xs uppercase tracking-[0.18em] text-stone-400">
                Sistem mantığı
              </p>
              <p className="mt-2 text-sm leading-7 text-stone-600">
                Kullanıcının veri derinliğine göre model seçimi otomatik değişir;
                böylece cold-start ve ileri seviye kişiselleştirme aynı akışta çözülür.
              </p>
            </div>

            <div className="space-y-3">
              {MODEL_ITEMS.map(([title, description]) => (
                <div
                  key={title}
                  className="rounded-2xl border border-stone-200/80 bg-stone-50/80 px-4 py-3"
                >
                  <p className="text-sm font-medium text-stone-900">{title}</p>
                  <p className="mt-1 text-sm leading-6 text-stone-500">
                    {description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="rounded-[2rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-6 py-7 shadow-[0_20px_50px_rgba(28,25,23,0.05)] md:px-8">
          <p className="text-xs uppercase tracking-[0.2em] text-stone-400">
            Neden güçlü?
          </p>
          <div className="mt-5 space-y-4">
            {[
              [
                "Cold-start çözümü var",
                "Yeni kullanıcılar için yalnızca profil verisiyle anlamlı öneriler üretilebilir.",
              ],
              [
                "Davranışla giderek iyileşir",
                "Puanlama geldikçe içerik ve collaborative filtering sinyalleri devreye girer.",
              ],
              [
                "Kategori bağlamını korur",
                "Her öneri isteği belirli bir kategori içinde değerlendirildiği için sonuçlar daha nettir.",
              ],
            ].map(([title, description]) => (
              <div key={title} className="rounded-[1.5rem] bg-stone-50/80 p-5">
                <p className="text-sm font-medium text-stone-900">{title}</p>
                <p className="mt-2 text-sm leading-7 text-stone-600">
                  {description}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-[2rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-6 py-7 shadow-[0_20px_50px_rgba(28,25,23,0.05)] md:px-8">
          <p className="text-xs uppercase tracking-[0.2em] text-stone-400">
            Akış
          </p>
          <div className="mt-5 grid gap-4 md:grid-cols-3">
            {[
              ["1", "Profil oluştur", "Cilt tipi, tonu ve alt ton bilgisi alınır."],
              ["2", "Kategori seç", "Keşfet ekranında ilgilendiğin ürün grubu belirlenir."],
              ["3", "Puanla ve geliştir", "Her yeni puanlama öneri kalitesini artırır."],
            ].map(([step, title, description]) => (
              <div
                key={step}
                className="rounded-[1.5rem] border border-stone-200 bg-stone-50/70 p-5"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[linear-gradient(135deg,var(--accent),var(--accent-deep))] text-sm font-medium text-white">
                  {step}
                </div>
                <p className="mt-4 text-sm font-medium text-stone-900">{title}</p>
                <p className="mt-2 text-sm leading-7 text-stone-500">
                  {description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
