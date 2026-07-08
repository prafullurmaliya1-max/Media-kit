// All API calls go through this file — never write fetch() inline in components

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Helper — wraps fetch with error handling
async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || "API error");
  }
  return res.json();
}

// --- Auth ---
export const api = {
  // Get logged-in creator's profile
  getMe: (userId) =>
    request(`/auth/me?user_id=${userId}`),

  // --- YouTube ---
  getYoutubeStats: (userId) =>
    request(`/youtube/stats/${userId}`),

  // --- Instagram ---
  getInstagramStats: (userId) =>
    request(`/instagram/stats/${userId}`),

  // --- Profile ---
  updateProfile: (userId, data) =>
    request(`/profile/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  updateRates: (userId, rates) =>
    request(`/profile/${userId}/rates`, {
      method: "PUT",
      body: JSON.stringify({ rates }),
    }),

  // Public kit — no user ID needed, just the slug
  getPublicKit: (slug) =>
    request(`/profile/kit/${slug}`),
};
