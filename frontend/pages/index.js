// Landing page — creator clicks "Connect YouTube" to start OAuth
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const handleLogin = () => {
    // Redirect to our FastAPI backend which then redirects to Google
    window.location.href = `${API_URL}/auth/google`;
  };

  return (
    <main style={{ minHeight: "100vh", display: "flex", alignItems: "center",
      justifyContent: "center", fontFamily: "sans-serif", background: "#f9f9f9" }}>
      <div style={{ textAlign: "center", maxWidth: 480, padding: "2rem" }}>
        <h1 style={{ fontSize: 32, fontWeight: 600, marginBottom: 12 }}>
          Creator Media Kit
        </h1>
        <p style={{ color: "#666", marginBottom: 32, lineHeight: 1.6 }}>
          Connect your YouTube and Instagram. Get a live, shareable analytics
          page you can send to brands in one link.
        </p>
        <button
          onClick={handleLogin}
          style={{
            background: "#1D9E75", color: "#fff", border: "none",
            padding: "14px 32px", borderRadius: 8, fontSize: 16,
            cursor: "pointer", fontWeight: 500,
          }}
        >
          Connect YouTube to get started →
        </button>
        <p style={{ marginTop: 16, fontSize: 13, color: "#999" }}>
          Read-only access · No posting on your behalf · Cancel anytime
        </p>
      </div>
    </main>
  );
}
