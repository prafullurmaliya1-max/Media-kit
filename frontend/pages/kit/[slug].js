import { useEffect, useState, useRef } from "react";
import { api } from "../../lib/api";

export async function getServerSideProps({ params }) {
  try {
    const kit = await api.getPublicKit(params.slug);
    return { props: { kit } };
  } catch {
    return { notFound: true };
  }
}

export default function PublicKit({ kit }) {
  const { creator, youtube, instagram, sponsorship_rates } = kit;
  const [activeTab, setActiveTab] = useState("youtube");
  const c1Ref = useRef(null);
  const c2Ref = useRef(null);
  const c3Ref = useRef(null);
  const c4Ref = useRef(null);
  const chartsRef = useRef({});

  const TEAL = "#1D9E75", BLUE = "#2a78d6", AMBER = "#eda100";
  const CORAL = "#D85A30", PURPLE = "#534AB7", GRAY = "#888780";
  const GRID = "#e1e0d9", TICK = "#898781";

  function fmt(n) {
    if (!n && n !== 0) return "—";
    if (typeof n === "string") return n;
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${Math.round(n / 1_000)}K`;
    return String(n);
  }

  const tabData = {
    youtube: {
      stats: youtube ? [
        { label: "Subscribers", value: fmt(youtube.subscriber_count), delta: "YouTube" },
        { label: "Avg views/video", value: fmt(youtube.avg_views_per_video), delta: "Recent avg" },
        { label: "Total videos", value: fmt(youtube.video_count), delta: "" },
        { label: "Engagement", value: youtube.engagement_rate ? `${youtube.engagement_rate}%` : "—", delta: "Likes/views" },
      ] : [],
      pie: { labels: ["18–24", "25–34", "35–44", "45+"], data: [42, 38, 14, 6], colors: [TEAL, BLUE, AMBER, GRAY] },
      countries: { labels: ["India", "US", "UK", "UAE", "Canada"], data: [58, 18, 10, 8, 6] },
      chart1Title: "Monthly views",
      chart2Title: "Age breakdown",
    },
    instagram: {
      stats: instagram ? [
        { label: "Followers", value: fmt(instagram.follower_count), delta: "Instagram" },
        { label: "Posts", value: fmt(instagram.media_count), delta: "" },
        { label: "Username", value: `@${instagram.username}`, delta: "" },
        { label: "Engagement", value: instagram.engagement_rate ? `${instagram.engagement_rate}%` : "—", delta: "" },
      ] : [],
      pie: { labels: ["Reels", "Posts", "Stories"], data: [60, 30, 10], colors: [TEAL, BLUE, AMBER] },
      countries: { labels: ["India", "US", "UK", "UAE", "Other"], data: [70, 12, 8, 5, 5] },
      chart1Title: "Monthly reach",
      chart2Title: "Content mix",
    },
    combined: {
      stats: [
        { label: "YouTube subs", value: fmt(youtube?.subscriber_count), delta: "YouTube" },
        { label: "Instagram followers", value: fmt(instagram?.follower_count), delta: "Instagram" },
        { label: "Total content", value: fmt((youtube?.video_count || 0) + (instagram?.media_count || 0)), delta: "All platforms" },
        { label: "Platforms", value: "2", delta: "Active" },
      ],
      pie: { labels: ["YouTube", "Instagram"], data: [62, 38], colors: [CORAL, PURPLE] },
      countries: { labels: ["India", "US", "UK", "UAE", "Canada"], data: [62, 16, 10, 7, 5] },
      chart1Title: "Combined reach",
      chart2Title: "Platform split",
    },
  };

  useEffect(() => {
    if (typeof window === "undefined") return;

    const script = document.createElement("script");
    script.src = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js";
    script.onload = () => renderCharts(activeTab);
    document.head.appendChild(script);

    return () => { destroyCharts(); };
  }, []);

  useEffect(() => {
    if (window.Chart) renderCharts(activeTab);
  }, [activeTab]);

  function destroyCharts() {
    Object.values(chartsRef.current).forEach(c => { if (c) c.destroy(); });
    chartsRef.current = {};
  }

  function renderCharts(tab) {
    if (!window.Chart) return;
    destroyCharts();
    const d = tabData[tab];
    const base = {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: TICK, font: { size: 11 } } },
        y: { grid: { color: GRID }, ticks: { color: TICK, font: { size: 11 } } }
      }
    };

    const months = ["Feb", "Mar", "Apr", "May", "Jun", "Jul"];
    const views = tab === "instagram" ? [0, 1, 1, 2, 2, 3] : tab === "combined" ? [8, 13, 16, 20, 24, 26] : [8, 12, 15, 18, 22, 23];
    const growth = tab === "instagram" ? [0, 1, 1, 2, 2, 3] : tab === "combined" ? [1, 3, 4, 5, 6, 8] : [1, 2, 3, 3, 4, 5];

    if (c1Ref.current) {
      chartsRef.current.c1 = new window.Chart(c1Ref.current, {
        type: "bar",
        data: { labels: months, datasets: [{ data: views, backgroundColor: TEAL, borderRadius: { topLeft: 4, topRight: 4 }, barThickness: 18 }] },
        options: { ...base }
      });
    }

    if (c2Ref.current) {
      chartsRef.current.c2 = new window.Chart(c2Ref.current, {
        type: "doughnut",
        data: { labels: d.pie.labels, datasets: [{ data: d.pie.data, backgroundColor: d.pie.colors, borderWidth: 2, borderColor: "#fff" }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.raw}%` } } }, cutout: "60%" }
      });
    }

    if (c3Ref.current) {
      chartsRef.current.c3 = new window.Chart(c3Ref.current, {
        type: "line",
        data: { labels: months, datasets: [{ data: growth, borderColor: BLUE, backgroundColor: "rgba(42,120,214,0.1)", fill: true, tension: 0.4, pointBackgroundColor: BLUE, pointRadius: 4, pointBorderColor: "#fff", pointBorderWidth: 2, borderWidth: 2 }] },
        options: { ...base }
      });
    }

    if (c4Ref.current) {
      chartsRef.current.c4 = new window.Chart(c4Ref.current, {
        type: "bar",
        data: { labels: d.countries.labels, datasets: [{ data: d.countries.data, backgroundColor: PURPLE, borderRadius: { topRight: 4, bottomRight: 4 }, barThickness: 14 }] },
        options: { indexAxis: "y", responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { color: GRID }, ticks: { color: TICK, font: { size: 11 }, callback: v => v + "%" } }, y: { grid: { display: false }, ticks: { color: TICK, font: { size: 11 } } } } }
      });
    }
  }

  const td = tabData[activeTab];

  return (
    <main style={s.page}>
      {/* Hero */}
      <div style={s.hero}>
        <div style={s.avatar}>
          {creator.avatar_url
            ? <img src={creator.avatar_url} alt={creator.name} style={{ width: "100%", height: "100%", objectFit: "cover", borderRadius: "50%" }} />
            : <span style={{ fontSize: 28, fontWeight: 500, color: "#fff" }}>{creator.name[0]}</span>}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={s.name}>{creator.name}</div>
          <div style={s.handle}>{creator.niche || "Content Creator"}</div>
          <div style={s.badges}>
            {(creator.niche || "Tech").split(",").map((n, i) => (
              <span key={i} style={{ ...s.badge, background: i === 0 ? "#E1F5EE" : i === 1 ? "#EEEDFE" : "#E6F1FB", color: i === 0 ? "#085041" : i === 1 ? "#3C3489" : "#0C447C" }}>{n.trim()}</span>
            ))}
          </div>
          {creator.location && <div style={s.muted}>📍 {creator.location}</div>}
        </div>
        <button style={s.shareBtn} onClick={() => { navigator.clipboard?.writeText(window.location.href); }}>
          Share kit ↗
        </button>
      </div>

      {/* Tabs */}
      <div style={s.tabs}>
        {["youtube", "instagram", "combined"].map(t => (
          <button key={t} style={{ ...s.tab, ...(activeTab === t ? s.tabActive : {}) }} onClick={() => setActiveTab(t)}>
            {t === "youtube" ? "YouTube" : t === "instagram" ? "Instagram" : "Overview"}
          </button>
        ))}
      </div>

      {/* Stat cards */}
      <div style={s.statsGrid}>
        {td.stats.map((st, i) => (
          <div key={i} style={s.statCard}>
            <div style={s.statLabel}>{st.label}</div>
            <div style={s.statValue}>{st.value}</div>
            {st.delta && <div style={s.statDelta}>{st.delta}</div>}
          </div>
        ))}
      </div>

      {/* Charts row 1 */}
      <div style={s.chartsRow}>
        <div style={s.chartCard}>
          <div style={s.chartTitle}>{td.chart1Title}</div>
          <div style={{ position: "relative", height: 170 }}>
            <canvas ref={c1Ref} role="img" aria-label="Monthly views chart" />
          </div>
        </div>
        <div style={s.chartCard}>
          <div style={s.chartTitle}>{td.chart2Title}</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 8 }}>
            {td.pie.labels.map((l, i) => (
              <span key={i} style={{ fontSize: 11, color: "#888", display: "flex", alignItems: "center", gap: 4 }}>
                <span style={{ width: 8, height: 8, borderRadius: 2, background: td.pie.colors[i], display: "inline-block" }} />
                {l} {td.pie.data[i]}%
              </span>
            ))}
          </div>
          <div style={{ position: "relative", height: 150 }}>
            <canvas ref={c2Ref} role="img" aria-label="Audience breakdown chart" />
          </div>
        </div>
      </div>

      {/* Charts row 2 */}
      <div style={s.chartsRow}>
        <div style={s.chartCard}>
          <div style={s.chartTitle}>Growth trend</div>
          <div style={{ position: "relative", height: 170 }}>
            <canvas ref={c3Ref} role="img" aria-label="Growth trend chart" />
          </div>
        </div>
        <div style={s.chartCard}>
          <div style={s.chartTitle}>Top countries</div>
          <div style={{ position: "relative", height: 170 }}>
            <canvas ref={c4Ref} role="img" aria-label="Top countries chart" />
          </div>
        </div>
      </div>

      {/* Contact + Rates */}
      <div style={s.twoCol}>
        <div style={s.section}>
          <div style={s.sectionTitle}>Contact & booking</div>
          {creator.contact_email && <InfoRow icon="✉" label="Email" val={creator.contact_email} accent />}
          {instagram?.username && <InfoRow icon="📸" label="Instagram" val={`@${instagram.username}`} />}
          {creator.location && <InfoRow icon="📍" label="Based in" val={creator.location} />}
          <InfoRow icon="🌐" label="Languages" val="Hindi, English" />
          <InfoRow icon="⚡" label="Response" val="Within 24 hrs" />
        </div>
        <div style={s.section}>
          <div style={s.sectionTitle}>Sponsorship rates</div>
          {sponsorship_rates?.length > 0
            ? sponsorship_rates.map((r, i) => (
              <div key={i} style={s.rateRow}>
                <span style={{ color: "#888", fontSize: 13 }}>{r.package_name}</span>
                <span style={{ fontWeight: 500, fontSize: 13 }}>{r.price}</span>
              </div>
            ))
            : ["Dedicated video", "Integration (60s)", "Instagram reel", "Story"].map((name, i) => (
              <div key={i} style={s.rateRow}>
                <span style={{ color: "#888", fontSize: 13 }}>{name}</span>
                <span style={{ fontWeight: 500, fontSize: 13 }}>Contact for rates</span>
              </div>
            ))
          }
        </div>
      </div>

      <p style={s.footer}>Stats auto-update every hour · {new Date().toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}</p>
    </main>
  );
}

function InfoRow({ icon, label, val, accent }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderBottom: "0.5px solid #eee", fontSize: 13 }}>
      <span style={{ color: "#aaa", width: 90, display: "flex", alignItems: "center", gap: 6 }}>{icon} {label}</span>
      <span style={{ fontWeight: 500, color: accent ? "#1D9E75" : "inherit" }}>{val}</span>
    </div>
  );
}

const s = {
  page: { maxWidth: 780, margin: "0 auto", padding: "2rem 1.25rem", fontFamily: "sans-serif", color: "#111" },
  hero: { display: "flex", gap: 16, alignItems: "flex-start", marginBottom: "1.5rem", paddingBottom: "1.5rem", borderBottom: "0.5px solid #eee", flexWrap: "wrap" },
  avatar: { width: 76, height: 76, borderRadius: "50%", background: "#1D9E75", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, overflow: "hidden" },
  name: { fontSize: 22, fontWeight: 600, marginBottom: 3 },
  handle: { fontSize: 13, color: "#888", marginBottom: 8 },
  badges: { display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 8 },
  badge: { fontSize: 11, padding: "3px 10px", borderRadius: 20, fontWeight: 500 },
  muted: { fontSize: 13, color: "#888" },
  shareBtn: { marginLeft: "auto", background: "#1D9E75", color: "#fff", border: "none", padding: "9px 18px", borderRadius: 8, fontSize: 13, cursor: "pointer", fontWeight: 500, flexShrink: 0 },
  tabs: { display: "flex", gap: 8, marginBottom: "1.25rem" },
  tab: { padding: "7px 16px", fontSize: 13, borderRadius: 20, cursor: "pointer", border: "0.5px solid #ddd", background: "transparent", color: "#888" },
  tabActive: { background: "#f5f5f5", color: "#111", borderColor: "#bbb", fontWeight: 500 },
  statsGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 10, marginBottom: "1.25rem" },
  statCard: { background: "#f7f7f7", borderRadius: 8, padding: "1rem" },
  statLabel: { fontSize: 11, color: "#888", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 },
  statValue: { fontSize: 22, fontWeight: 600 },
  statDelta: { fontSize: 11, color: "#1D9E75", marginTop: 4 },
  chartsRow: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: "1rem" },
  chartCard: { background: "#fff", border: "0.5px solid #eee", borderRadius: 12, padding: "1rem 1.25rem" },
  chartTitle: { fontSize: 13, fontWeight: 500, marginBottom: 10 },
  twoCol: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: "1rem" },
  section: { background: "#fff", border: "0.5px solid #eee", borderRadius: 12, padding: "1rem 1.25rem" },
  sectionTitle: { fontSize: 14, fontWeight: 500, marginBottom: 12 },
  rateRow: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "9px 0", borderBottom: "0.5px solid #eee" },
  footer: { textAlign: "center", color: "#bbb", fontSize: 11, marginTop: "1.5rem" },
};