"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { ApiError, api, type OfflineEvaluationResponse, type RecommendationMetricsResponse } from "../../lib/api";

const METRIC_LABELS: Record<string, string> = {
  precision_at_10: "Precision@10 lideri",
  hit_rate_at_10: "Hit Rate@10 lideri",
  ndcg_at_10: "NDCG@10 lideri",
  auc: "AUC lideri",
  coverage: "Coverage lideri",
  diversity: "Diversity lideri",
};

const ONLINE_MODEL_LABELS: Record<string, string> = {
  lightfm: "LightFM",
  content_seeded: "Content Seeded",
  profile: "Profile",
  popularity: "Popularity",
  hybrid: "Hybrid",
  hybrid_fallback_popularity: "Popularity Fallback",
};

function formatPercent(value: number | null | undefined) {
  if (value == null) return "--";
  return `%${(value * 100).toFixed(1)}`;
}

function formatScore(value: number | null | undefined) {
  if (value == null) return "--";
  return value.toFixed(3);
}

function normalizeLabel(value: string | null | undefined) {
  if (!value) return "--";
  return value.toLowerCase().replace(/\s+/g, "-");
}

function formatCompactNumber(value: number | null | undefined) {
  if (value == null) return "--";
  return new Intl.NumberFormat("tr-TR", {
    notation: value >= 1000 ? "compact" : "standard",
    maximumFractionDigits: 1,
  }).format(value);
}

function toBarWidth(value: number | null | undefined, maxValue: number) {
  if (value == null || maxValue <= 0) return 0;
  return Math.max(8, Math.round((value / maxValue) * 100));
}

function BarRow({
  label,
  valueLabel,
  width,
  tone = "amber",
  helper,
}: {
  label: string;
  valueLabel: string;
  width: number;
  tone?: "amber" | "stone";
  helper?: string;
}) {
  const toneClass =
    tone === "amber"
      ? "bg-[linear-gradient(90deg,var(--accent),var(--accent-deep))]"
      : "bg-[linear-gradient(90deg,#8d8176,#3f3934)]";

  return (
    <div className="space-y-2">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-stone-900">{label}</p>
          {helper ? (
            <p className="text-xs text-stone-400">{helper}</p>
          ) : null}
        </div>
        <span className="text-sm font-medium text-stone-700">{valueLabel}</span>
      </div>
      <div className="h-2.5 overflow-hidden rounded-full bg-stone-100">
        <div
          className={`h-full rounded-full transition-all duration-500 ${toneClass}`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, token, loading, isAdmin } = useAuth();
  const [onlineMetrics, setOnlineMetrics] = useState<RecommendationMetricsResponse | null>(null);
  const [offlineMetrics, setOfflineMetrics] = useState<OfflineEvaluationResponse | null>(null);
  const [pageError, setPageError] = useState("");
  const [fetching, setFetching] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  async function loadDashboardData(activeToken: string) {
    const [online, offline] = await Promise.all([
      api.getRecommendationMetrics(activeToken),
      api.getOfflineModelEvaluation(activeToken),
    ]);
    setOnlineMetrics(online);
    setOfflineMetrics(offline);
    setPageError("");
  }

  useEffect(() => {
    if (!loading && !user) router.replace("/");
    if (!loading && user && !isAdmin) router.replace("/explore");
  }, [loading, user, isAdmin, router]);

  useEffect(() => {
    if (!token || !isAdmin) return;
    let cancelled = false;
    loadDashboardData(token)
      .then(() => {
        if (cancelled) return;
      })
      .catch((err) => {
        if (cancelled) return;
        setPageError(
          err instanceof ApiError ? err.message : "Dashboard verileri yüklenemedi.",
        );
      })
      .finally(() => {
        if (!cancelled) setFetching(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token, isAdmin]);

  async function handleRefresh() {
    if (!token || refreshing) return;
    setRefreshing(true);
    try {
      await loadDashboardData(token);
    } catch (err) {
      setPageError(
        err instanceof ApiError ? err.message : "Dashboard verileri yenilenemedi.",
      );
    } finally {
      setRefreshing(false);
    }
  }

  const bestOnlineModel = useMemo(() => {
    if (!onlineMetrics?.model_metrics?.length) return null;
    return [...onlineMetrics.model_metrics].sort((a, b) => {
      const conversionA = a.rating_conversion ?? -1;
      const conversionB = b.rating_conversion ?? -1;
      if (conversionB !== conversionA) return conversionB - conversionA;
      return (b.average_attributed_rating ?? -1) - (a.average_attributed_rating ?? -1);
    })[0];
  }, [onlineMetrics]);

  const bestOfflineModel = useMemo(() => {
    if (!offlineMetrics?.rows?.length) return null;
    return [...offlineMetrics.rows].sort((a, b) => b.precision_at_10 - a.precision_at_10)[0];
  }, [offlineMetrics]);

  const onlineLeaderboard = useMemo(() => {
    if (!onlineMetrics?.model_metrics?.length) return [];
    return [...onlineMetrics.model_metrics].sort((a, b) => {
      const conversionA = a.rating_conversion ?? -1;
      const conversionB = b.rating_conversion ?? -1;
      if (conversionB !== conversionA) return conversionB - conversionA;
      return (b.ctr ?? -1) - (a.ctr ?? -1);
    });
  }, [onlineMetrics]);

  const offlineLeaderboard = useMemo(() => {
    if (!offlineMetrics?.rows?.length) return [];
    return [...offlineMetrics.rows].sort((a, b) => b.precision_at_10 - a.precision_at_10);
  }, [offlineMetrics]);

  const onlineMaxConversion = useMemo(
    () => Math.max(0, ...onlineLeaderboard.map((item) => item.rating_conversion ?? 0)),
    [onlineLeaderboard],
  );

  const offlineMaxPrecision = useMemo(
    () => Math.max(0, ...offlineLeaderboard.map((item) => item.precision_at_10)),
    [offlineLeaderboard],
  );

  const bestRankRow = useMemo(() => {
    if (!onlineMetrics?.rank_metrics?.length) return null;
    return [...onlineMetrics.rank_metrics].sort((a, b) => {
      const ctrA = a.ctr ?? -1;
      const ctrB = b.ctr ?? -1;
      if (ctrB !== ctrA) return ctrB - ctrA;
      return (b.rating_conversion ?? -1) - (a.rating_conversion ?? -1);
    })[0];
  }, [onlineMetrics]);

  const modelAlignment = useMemo(() => {
    const online = normalizeLabel(bestOnlineModel?.model_used);
    const offline = normalizeLabel(bestOfflineModel?.model);
    if (online === "--" || offline === "--") return "Yetersiz veri";
    return online.includes("lightfm") && offline.includes("lightfm")
      ? "Online ve offline liderler hizalı"
      : "Canlı davranış ile offline lider farklı";
  }, [bestOnlineModel, bestOfflineModel]);

  if (loading || fetching) {
    return (
      <div className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center text-sm text-stone-400">
        Dashboard yükleniyor…
      </div>
    );
  }

  if (!user || !isAdmin) return null;

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-8 px-5 py-8 md:px-6 md:py-10">
      <section className="overflow-hidden rounded-[2rem] border border-[color:var(--border-strong)] bg-[linear-gradient(135deg,rgba(255,255,255,0.96),rgba(244,233,218,0.95))] shadow-[0_30px_80px_rgba(28,25,23,0.07)]">
        <div className="grid gap-8 px-6 py-8 md:grid-cols-[1.15fr_0.85fr] md:px-8 md:py-10">
          <div className="space-y-5">
            <div className="flex flex-wrap items-center gap-3">
              <div className="inline-flex w-fit items-center gap-2 rounded-full border border-white/80 bg-white/75 px-3 py-1 text-[11px] uppercase tracking-[0.22em] text-stone-500 shadow-sm">
                <span className="h-2 w-2 rounded-full bg-[var(--accent)]" />
                Admin evaluation dashboard
              </div>
              <button
                type="button"
                onClick={handleRefresh}
                disabled={refreshing}
                aria-label="Dashboard verilerini yenile"
                title="Dashboard verilerini yenile"
                className="flex h-10 w-10 items-center justify-center rounded-full border border-stone-200 bg-white/90 text-stone-700 shadow-sm transition-all hover:-translate-y-0.5 hover:border-stone-400 hover:text-stone-900 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <span
                  className={`text-base leading-none ${refreshing ? "animate-spin" : ""}`}
                  aria-hidden="true"
                >
                  ↻
                </span>
              </button>
            </div>
            <div className="space-y-3">
              <h1 className="text-3xl font-light leading-tight text-stone-900 md:text-5xl">
                Online davranış ile
                <span className="block text-[color:var(--accent-deep)]">
                  offline model kalitesini aynı ekranda oku
                </span>
              </h1>
              <p className="max-w-3xl text-sm leading-7 text-stone-600 md:text-[15px]">
                Bu panel yalnızca admin oturumu için açıktır. Recommendation event,
                click ve 24 saatlik attribution verileri burada toplanır; yanında da
                notebook tabanlı offline evaluation sonuçları gösterilir.
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
                <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                  Admin hesap
                </p>
                <p className="mt-2 truncate text-sm font-medium text-stone-900">
                  {user.email}
                </p>
              </div>
              <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
                <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                  Online event
                </p>
                <p className="mt-2 text-2xl font-light text-stone-900">
                  {onlineMetrics?.total_recommendation_events ?? 0}
                </p>
              </div>
              <div className="rounded-2xl border border-white/70 bg-white/80 p-4 shadow-sm">
                <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                  Offline model
                </p>
                <p className="mt-2 text-2xl font-light text-stone-900">
                  {offlineMetrics?.rows.length ?? 0}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-[1.75rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)]/92 p-5 shadow-[0_18px_50px_rgba(28,25,23,0.08)]">
            <p className="text-xs uppercase tracking-[0.18em] text-stone-400">
              Hızlı yorum
            </p>
            <div className="mt-4 space-y-4">
              <div className="rounded-2xl bg-stone-50 p-4">
                <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                  Online en güçlü model
                </p>
                <p className="mt-2 text-lg font-medium text-stone-900">
                  {bestOnlineModel?.model_used ?? "--"}
                </p>
                <p className="mt-2 text-sm leading-7 text-stone-600">
                  Conversion {formatPercent(bestOnlineModel?.rating_conversion)} ve
                  ortalama attributed rating {formatScore(bestOnlineModel?.average_attributed_rating)} ile öne çıkıyor.
                </p>
              </div>
              <div className="rounded-2xl bg-stone-50 p-4">
                <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                  Offline en güçlü model
                </p>
                <p className="mt-2 text-lg font-medium text-stone-900">
                  {bestOfflineModel?.model ?? "--"}
                </p>
                <p className="mt-2 text-sm leading-7 text-stone-600">
                  Precision@10 {formatPercent(bestOfflineModel?.precision_at_10)} ve
                  NDCG@10 {formatPercent(bestOfflineModel?.ndcg_at_10)} ile veri seti üzerinde lider görünüyor.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {pageError && (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {pageError}
        </div>
      )}

      <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[1.75rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-5 py-5 shadow-[0_16px_40px_rgba(28,25,23,0.05)]">
          <div className="flex flex-wrap gap-2">
            {[
              `Attribution penceresi: ${onlineMetrics?.attribution_window_hours ?? 24} saat`,
              "Kaynak: canlı event tracking",
              "Offline kaynak: final evaluation csv",
              `Admin mode: ${user.email}`,
            ].map((chip) => (
              <span
                key={chip}
                className="rounded-full border border-stone-200 bg-stone-50 px-3 py-1.5 text-xs text-stone-600"
              >
                {chip}
              </span>
            ))}
          </div>
          <div className="mt-5 grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl bg-[linear-gradient(135deg,rgba(250,245,239,1),rgba(255,255,255,1))] p-4">
              <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                Online winner
              </p>
              <p className="mt-2 text-lg font-medium text-stone-900">
                {ONLINE_MODEL_LABELS[bestOnlineModel?.model_used ?? ""] ?? bestOnlineModel?.model_used ?? "--"}
              </p>
              <p className="mt-1 text-xs leading-6 text-stone-500">
                Conversion {formatPercent(bestOnlineModel?.rating_conversion)}
              </p>
            </div>
            <div className="rounded-2xl bg-[linear-gradient(135deg,rgba(245,242,238,1),rgba(255,255,255,1))] p-4">
              <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                Offline winner
              </p>
              <p className="mt-2 text-lg font-medium text-stone-900">
                {bestOfflineModel?.model ?? "--"}
              </p>
              <p className="mt-1 text-xs leading-6 text-stone-500">
                Precision@10 {formatPercent(bestOfflineModel?.precision_at_10)}
              </p>
            </div>
            <div className="rounded-2xl bg-[linear-gradient(135deg,rgba(255,249,240,1),rgba(250,241,229,1))] p-4">
              <p className="text-[11px] uppercase tracking-[0.16em] text-amber-700">
                Alignment
              </p>
              <p className="mt-2 text-sm font-medium text-stone-900">
                {modelAlignment}
              </p>
              <p className="mt-1 text-xs leading-6 text-stone-500">
                Canlı davranış ile dataset performansı aynı modeli işaret ediyor mu sorusuna hızlı cevap.
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-[1.75rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-5 py-5 shadow-[0_16px_40px_rgba(28,25,23,0.05)]">
          <p className="text-xs uppercase tracking-[0.18em] text-stone-400">
            Dashboard okuma notu
          </p>
          <div className="mt-4 space-y-3">
            {[
              ["Online", "Gerçek kullanıcı click ve rating davranışını okur."],
              ["Offline", "Notebook evaluation ile model kalitesini veri setinde karşılaştırır."],
              ["Rank", "Liste sırasının gerçek etkileşimi ne kadar etkilediğini gösterir."],
            ].map(([title, desc]) => (
              <div key={title} className="rounded-2xl border border-stone-200 bg-stone-50/70 p-4">
                <p className="text-sm font-medium text-stone-900">{title}</p>
                <p className="mt-1 text-sm leading-6 text-stone-500">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-4">
        {[
          ["İmpression", formatCompactNumber(onlineMetrics?.total_impressions)],
          ["Click", formatCompactNumber(onlineMetrics?.total_clicks)],
          ["CTR", formatPercent(onlineMetrics?.overall_ctr)],
          ["Rating conversion", formatPercent(onlineMetrics?.overall_rating_conversion)],
        ].map(([label, value]) => (
          <div
            key={label}
            className="rounded-[1.5rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] p-5 shadow-[0_16px_40px_rgba(28,25,23,0.05)]"
          >
            <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
              {label}
            </p>
            <p className="mt-3 text-3xl font-light text-stone-900">
              {value}
            </p>
          </div>
        ))}
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="rounded-[2rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-6 py-7 shadow-[0_20px_50px_rgba(28,25,23,0.05)] md:px-8">
          <div className="mb-5 flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-stone-400">
                Online model leaderboard
              </p>
              <p className="mt-2 text-sm leading-7 text-stone-500">
                24 saatlik attribution içinde en çok dönüşüm üreten modeller.
              </p>
            </div>
            <div className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-800">
              canlı davranış
            </div>
          </div>
          <div className="space-y-4">
            {onlineLeaderboard.map((row, index) => (
              <div
                key={row.model_used}
                className="rounded-[1.5rem] border border-stone-200 bg-stone-50/70 p-4"
              >
                <div className="mb-3 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-xs font-semibold text-stone-700 shadow-sm">
                      #{index + 1}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-stone-900">
                        {ONLINE_MODEL_LABELS[row.model_used] ?? row.model_used}
                      </p>
                      <p className="text-xs text-stone-400">
                        {row.recommendation_events} event, {row.impressions} impression
                      </p>
                    </div>
                  </div>
                  <div className="rounded-full bg-white px-3 py-1 text-xs font-medium text-stone-700 shadow-sm">
                    avg {formatScore(row.average_attributed_rating)}
                  </div>
                </div>
                <div className="space-y-3">
                  <BarRow
                    label="Rating conversion"
                    valueLabel={formatPercent(row.rating_conversion)}
                    width={toBarWidth(row.rating_conversion, onlineMaxConversion)}
                  />
                  <BarRow
                    label="CTR"
                    valueLabel={formatPercent(row.ctr)}
                    width={toBarWidth(row.ctr, 1)}
                    tone="stone"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-[2rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-6 py-7 shadow-[0_20px_50px_rgba(28,25,23,0.05)] md:px-8">
          <div className="mb-5 flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-stone-400">
                Offline model leaderboard
              </p>
              <p className="mt-2 text-sm leading-7 text-stone-500">
                Veri seti üzerinde Precision@10 bazlı sıralama ve kalite farkı.
              </p>
            </div>
            <div className="rounded-full bg-stone-100 px-3 py-1 text-xs font-medium text-stone-700">
              evaluation csv
            </div>
          </div>
          <div className="space-y-4">
            {offlineLeaderboard.map((row, index) => (
              <div
                key={row.model}
                className="rounded-[1.5rem] border border-stone-200 bg-stone-50/70 p-4"
              >
                <div className="mb-3 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-xs font-semibold text-stone-700 shadow-sm">
                      #{index + 1}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-stone-900">{row.model}</p>
                      <p className="text-xs text-stone-400">
                        NDCG {formatPercent(row.ndcg_at_10)} • AUC {formatPercent(row.auc)}
                      </p>
                    </div>
                  </div>
                  <div className="rounded-full bg-white px-3 py-1 text-xs font-medium text-stone-700 shadow-sm">
                    div {formatPercent(row.diversity)}
                  </div>
                </div>
                <div className="space-y-3">
                  <BarRow
                    label="Precision@10"
                    valueLabel={formatPercent(row.precision_at_10)}
                    width={toBarWidth(row.precision_at_10, offlineMaxPrecision)}
                  />
                  <BarRow
                    label="Coverage"
                    valueLabel={formatPercent(row.coverage)}
                    width={toBarWidth(row.coverage, 1)}
                    tone="stone"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="rounded-[2rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-6 py-7 shadow-[0_20px_50px_rgba(28,25,23,0.05)] md:px-8">
          <div className="mb-5">
            <p className="text-xs uppercase tracking-[0.2em] text-stone-400">
              Online model performansı
            </p>
            <p className="mt-2 text-sm leading-7 text-stone-500">
              Recommendation event, click ve 24 saat içinde ilişkilendirilen rating verileri.
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-stone-400">
                <tr>
                  <th className="pb-3 pr-4 font-medium">Model</th>
                  <th className="pb-3 pr-4 font-medium">Event</th>
                  <th className="pb-3 pr-4 font-medium">CTR</th>
                  <th className="pb-3 pr-4 font-medium">Conversion</th>
                  <th className="pb-3 pr-4 font-medium">Positive rate</th>
                  <th className="pb-3 pr-4 font-medium">Avg rating</th>
                </tr>
              </thead>
              <tbody>
                {onlineMetrics?.model_metrics.map((row) => (
                  <tr key={row.model_used} className="border-t border-stone-100 text-stone-700">
                    <td className="py-3 pr-4 font-medium text-stone-900">{row.model_used}</td>
                    <td className="py-3 pr-4">{row.recommendation_events}</td>
                    <td className="py-3 pr-4">{formatPercent(row.ctr)}</td>
                    <td className="py-3 pr-4">{formatPercent(row.rating_conversion)}</td>
                    <td className="py-3 pr-4">{formatPercent(row.positive_rating_rate)}</td>
                    <td className="py-3 pr-4">{formatScore(row.average_attributed_rating)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="rounded-[2rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-6 py-7 shadow-[0_20px_50px_rgba(28,25,23,0.05)] md:px-8">
          <div className="mb-5">
            <p className="text-xs uppercase tracking-[0.2em] text-stone-400">
              Offline leader board
            </p>
            <p className="mt-2 text-sm leading-7 text-stone-500">
              `outputs/model_comparison_final.csv` üzerinden üretilen karşılaştırma.
            </p>
          </div>
          <div className="space-y-3">
            {offlineMetrics?.leaders.map((leader) => (
              <div
                key={leader.metric}
                className="rounded-[1.5rem] border border-stone-200 bg-stone-50/70 p-4"
              >
                <p className="text-[11px] uppercase tracking-[0.16em] text-stone-400">
                  {METRIC_LABELS[leader.metric] ?? leader.metric}
                </p>
                <p className="mt-2 text-sm font-medium text-stone-900">
                  {leader.model}
                </p>
                <p className="mt-1 text-sm text-stone-600">
                  {formatPercent(leader.value)}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="rounded-[2rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-6 py-7 shadow-[0_20px_50px_rgba(28,25,23,0.05)] md:px-8">
          <div className="mb-5">
            <p className="text-xs uppercase tracking-[0.2em] text-stone-400">
              Offline model comparison
            </p>
            <p className="mt-2 text-sm leading-7 text-stone-500">
              Precision, NDCG, AUC, coverage ve diversity değerleri model bazında listelenir.
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-stone-400">
                <tr>
                  <th className="pb-3 pr-4 font-medium">Model</th>
                  <th className="pb-3 pr-4 font-medium">P@10</th>
                  <th className="pb-3 pr-4 font-medium">NDCG@10</th>
                  <th className="pb-3 pr-4 font-medium">AUC</th>
                  <th className="pb-3 pr-4 font-medium">Coverage</th>
                  <th className="pb-3 pr-4 font-medium">Diversity</th>
                </tr>
              </thead>
              <tbody>
                {offlineMetrics?.rows.map((row) => (
                  <tr key={row.model} className="border-t border-stone-100 text-stone-700">
                    <td className="py-3 pr-4 font-medium text-stone-900">{row.model}</td>
                    <td className="py-3 pr-4">{formatPercent(row.precision_at_10)}</td>
                    <td className="py-3 pr-4">{formatPercent(row.ndcg_at_10)}</td>
                    <td className="py-3 pr-4">{formatPercent(row.auc)}</td>
                    <td className="py-3 pr-4">{formatPercent(row.coverage)}</td>
                    <td className="py-3 pr-4">{formatPercent(row.diversity)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="rounded-[2rem] border border-[color:var(--border-strong)] bg-[color:var(--surface)] px-6 py-7 shadow-[0_20px_50px_rgba(28,25,23,0.05)] md:px-8">
          <div className="mb-5">
            <p className="text-xs uppercase tracking-[0.2em] text-stone-400">
              Rank davranışı
            </p>
            <p className="mt-2 text-sm leading-7 text-stone-500">
              Üst sıralar gerçekten daha çok click ve rating alıyor mu sorusuna bakar.
            </p>
          </div>
          {bestRankRow ? (
            <div className="mb-5 rounded-[1.5rem] border border-amber-100 bg-[linear-gradient(135deg,rgba(255,249,240,1),rgba(250,241,229,1))] p-4">
              <p className="text-[11px] uppercase tracking-[0.16em] text-amber-700">
                En dikkat çeken sıra
              </p>
              <p className="mt-2 text-lg font-medium text-stone-900">
                #{bestRankRow.rank} sıradaki ürünler
              </p>
              <p className="mt-2 text-sm leading-7 text-stone-600">
                CTR {formatPercent(bestRankRow.ctr)} ve conversion {formatPercent(bestRankRow.rating_conversion)} ile
                şu an en güçlü davranış sinyalini üretiyor.
              </p>
            </div>
          ) : null}
          {onlineMetrics?.rank_metrics?.length ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-stone-100">
                    <th className="pb-3 pr-4 text-xs font-medium uppercase tracking-[0.14em] text-stone-400">Sıra</th>
                    <th className="pb-3 pr-4 text-xs font-medium uppercase tracking-[0.14em] text-stone-400">Impression</th>
                    <th className="pb-3 pr-4 text-xs font-medium uppercase tracking-[0.14em] text-stone-400">CTR</th>
                    <th className="pb-3 pr-4 text-xs font-medium uppercase tracking-[0.14em] text-stone-400">Conversion</th>
                    <th className="pb-3 text-xs font-medium uppercase tracking-[0.14em] text-stone-400">Avg rating</th>
                  </tr>
                </thead>
                <tbody>
                  {onlineMetrics.rank_metrics.map((row) => {
                    const isBest = row.rank === bestRankRow?.rank;
                    return (
                      <tr
                        key={row.rank}
                        className={`border-t border-stone-100 ${isBest ? "bg-amber-50/60" : ""}`}
                      >
                        <td className="py-3 pr-4">
                          <span className={`inline-flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${isBest ? "bg-amber-100 text-amber-800" : "bg-stone-100 text-stone-600"}`}>
                            {row.rank}
                          </span>
                        </td>
                        <td className="py-3 pr-4 text-stone-600">{row.impressions}</td>
                        <td className="py-3 pr-4 font-medium text-stone-800">{formatPercent(row.ctr)}</td>
                        <td className="py-3 pr-4 font-medium text-stone-800">{formatPercent(row.rating_conversion)}</td>
                        <td className="py-3 text-stone-600">{formatScore(row.average_attributed_rating)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-stone-400">Henüz rank verisi yok.</p>
          )}
        </div>
      </section>
    </div>
  );
}
