import type { RecommendationPath } from "../lib/api";

interface Props {
  model: RecommendationPath;
  explanation: string;
}

const META: Record<RecommendationPath, { label: string; color: string }> = {
  lightfm: {
    label: "LightFM Collaborative Filtering",
    color: "bg-cyan-50 text-cyan-800 border-cyan-200",
  },
  hybrid: {
    label: "Hybrid — CF + İçerik",
    color: "bg-emerald-50 text-emerald-800 border-emerald-200",
  },
  content_seeded: {
    label: "İçerik Tabanlı (Puanlamalarından)",
    color: "bg-blue-50 text-blue-800 border-blue-200",
  },
  profile: {
    label: "Profil Tabanlı",
    color: "bg-amber-50 text-amber-800 border-amber-200",
  },
  popularity: {
    label: "Popülerlik Bazlı",
    color: "bg-stone-100 text-stone-700 border-stone-200",
  },
  hybrid_fallback_popularity: {
    label: "Popülerlik (Kategori Fallback)",
    color: "bg-orange-50 text-orange-800 border-orange-200",
  },
};

export function ModelBadge({ model, explanation }: Props) {
  const meta = META[model] ?? META.popularity;
  return (
    <div className="flex flex-col gap-2">
      <div
        className={`inline-flex items-center gap-2 px-3 py-1.5 border text-xs font-medium w-fit ${meta.color}`}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-current opacity-60" />
        {meta.label}
      </div>
      {explanation && (
        <p className="text-xs text-stone-500 max-w-2xl leading-relaxed">
          {explanation}
        </p>
      )}
    </div>
  );
}
