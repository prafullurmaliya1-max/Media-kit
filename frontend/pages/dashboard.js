import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { api } from "../lib/api";

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Dashboard() {
  const router = useRouter();
  const { user_id } = router.query;

  const [user, setUser] = useState(null);
  const [ytStats, setYtStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!user_id) return;

    async function loadData() {
      try {
        // Load user profile and YouTube stats in parallel
        const [userData, youtubeData] = await Promise.all([
          api.getMe(user_id),
          api.getYoutubeStats(user_id),
        ]);
        setUser(userData);
        setYtStats(youtubeData.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [user_id]);

  if (loading) return <div style={styles.center}>Loading your stats...</div>;
  if (error) return <div style={styles.center}>Error: {error}</div>;
  if (!user) return <div style={styles.center}>Not found</div>;

  const kitUrl = `${APP_URL}/kit/${user.slug}`;

  return (
    <main style={styles.page}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.h1}>Welcome, {user.name}</h1>
          <p style={styles.muted}>Your media kit is live at:</p>
          <a href={kitUrl} target="_blank" style={styles.kitLink}>{kitUrl}</a>
        </div>
        <button
          onClick={() => navigator.clipboard.writeText(kitUrl)}
          style={styles.btn}
        >
          Copy kit link
        </button>
      </div>

      {/* Connect Instagram (if not connected) */}
      <div style={styles.card}>
        <h2 style={styles.h2}>Connect Instagram</h2>
        <p style={styles.muted}>Add Instagram stats to your media kit.</p>
        <a href={`${API_URL}/instagram/connect?user_id=${user_id}`} style={styles.btn}>
          Connect Instagram
        </a>
      </div>

      {/* YouTube Stats */}
      {ytStats && (
        <div style={styles.card}>
          <h2 style={styles.h2}>YouTube — {ytStats.channel_name}</h2>
          <div style={styles.statsGrid}>
            <StatBox label="Subscribers" value={fmt(ytStats.subscriber_count)} />
            <StatBox label="Avg views/video" value={fmt(ytStats.avg_views_per_video)} />
            <StatBox label="Total videos" value={fmt(ytStats.video_count)} />
            <StatBox label="Engagement" value={`${ytStats.engagement_rate}%`} />
          </div>
        </div>
      )}
    </main>
  );
}

function StatBox({ label, value }) {
  return (
    <div style={styles.statBox}>
      <div style={styles.statLabel}>{label}</div>
      <div style={styles.statValue}>{value}</div>
    </div>
  );
}

// Format big numbers: 248000 → 248K
function fmt(n) {
  if (!n) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${Math.round(n / 1_000)}K`;
  return String(n);
}

const styles = {
  page: { maxWidth: 860, margin: "0 auto", padding: "2rem", fontFamily: "sans-serif" },
  center: { display: "flex", alignItems: "center", justifyContent: "center",
    minHeight: "100vh", fontFamily: "sans-serif" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "flex-start",
    marginBottom: "1.5rem", flexWrap: "wrap", gap: 12 },
  h1: { fontSize: 24, fontWeight: 600, margin: "0 0 4px" },
  h2: { fontSize: 18, fontWeight: 500, margin: "0 0 8px" },
  muted: { color: "#888", fontSize: 14, margin: "0 0 4px" },
  kitLink: { color: "#1D9E75", fontSize: 14, textDecoration: "none", fontWeight: 500 },
  card: { background: "#fff", border: "1px solid #eee", borderRadius: 12,
    padding: "1.25rem 1.5rem", marginBottom: "1rem" },
  statsGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
    gap: 12, marginTop: 12 },
  statBox: { background: "#f5f5f5", borderRadius: 8, padding: "1rem" },
  statLabel: { fontSize: 12, color: "#888", marginBottom: 6, textTransform: "uppercase",
    letterSpacing: "0.04em" },
  statValue: { fontSize: 22, fontWeight: 600 },
  btn: { background: "#1D9E75", color: "#fff", border: "none", padding: "10px 20px",
    borderRadius: 8, fontSize: 14, cursor: "pointer", fontWeight: 500,
    textDecoration: "none", display: "inline-block" },
};
