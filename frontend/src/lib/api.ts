const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Types ─────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserProfile {
  id: number;
  email: string;
  skin_type: string;
  skin_tone: string;
  undertone: string;
  created_at: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  skin_type: string;
  skin_tone: string;
  undertone: string;
}

export interface RecommendationItem {
  product_id: string;
  product_name: string;
  brand_name: string;
  primary_category: string;
  secondary_category: string;
  tertiary_category: string;
  price_usd: number | null;
  rating: number | null;
  score: number | null;
}

export type RecommendationPath =
  | "lightfm"
  | "hybrid"
  | "content_seeded"
  | "profile"
  | "popularity"
  | "hybrid_fallback_popularity";

export interface RecommendResponse {
  model_used: RecommendationPath;
  model_explanation: string;
  total_recommendations: number;
  recommendations: RecommendationItem[];
}

export interface RateResponse {
  product_id: string;
  rating: number;
  created_at: string;
}

export interface RatedProductDetail {
  product_id: string;
  rating: number;
  rated_at: string;
  product_name: string;
  brand_name: string;
  tertiary_category: string;
  price_usd: number | null;
}

export interface UpdateProfilePayload {
  skin_type?: string;
  skin_tone?: string;
  undertone?: string;
}

// ── Helpers ────────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch { /* ignore */ }
    throw new ApiError(res.status, detail);
  }

  return res.json() as Promise<T>;
}

// ── API calls ──────────────────────────────────────────────────────────────

export const api = {
  register: (p: RegisterPayload): Promise<UserProfile> =>
    request("/auth/register", { method: "POST", body: JSON.stringify(p) }),

  login: (email: string, password: string): Promise<TokenResponse> =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),

  getMe: (token: string): Promise<UserProfile> =>
    request("/users/me", {}, token),

  getCategories: (): Promise<{ categories: string[] }> =>
    request("/categories"),

  getRecommendations: (token: string, category: string, top_n = 10): Promise<RecommendResponse> =>
    request("/recommendations", { method: "POST", body: JSON.stringify({ category, top_n }) }, token),

  rateProduct: (token: string, product_id: string, rating: number): Promise<RateResponse> =>
    request("/interactions/rate", { method: "POST", body: JSON.stringify({ product_id, rating }) }, token),

  getMyInteractions: (token: string): Promise<RateResponse[]> =>
    request("/interactions/mine", {}, token),

  getMyInteractionsDetailed: (token: string): Promise<RatedProductDetail[]> =>
    request("/interactions/mine/detailed", {}, token),

  updateProfile: (token: string, payload: UpdateProfilePayload): Promise<UserProfile> =>
    request("/users/me", { method: "PATCH", body: JSON.stringify(payload) }, token),
};
