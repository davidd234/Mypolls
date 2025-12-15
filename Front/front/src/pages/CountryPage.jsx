import { useParams } from "react-router-dom";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";

/* MOCK DATA – ulterior îl legăm la API */
const COUNTRY_DATA = {
  ro: {
    name: "Romania",
    flag: "🇷🇴",
    stockIndex: "BET",
    stockValue: "+0.84%",
    news: [
      "Government adopts new fiscal package",
      "Presidential approval rating rises",
      "Opposition calls for early elections",
    ],
  },
  fr: {
    name: "France",
    flag: "🇫🇷",
    stockIndex: "CAC 40",
    stockValue: "-0.32%",
    news: [
      "Parliament debates pension reform",
      "Protests continue in major cities",
      "EU budget negotiations intensify",
    ],
  },
  de: {
    name: "Germany",
    flag: "🇩🇪",
    stockIndex: "DAX",
    stockValue: "+1.12%",
    news: [
      "Coalition tensions increase",
      "Industrial output exceeds forecasts",
      "AfD gains in regional polls",
    ],
  },
};

export default function CountryPage() {
  const { code } = useParams();
  const data = COUNTRY_DATA[code] || {
    name: code?.toUpperCase(),
    flag: "🏳️",
    stockIndex: "N/A",
    stockValue: "—",
    news: [],
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0b0f14",
        color: "#e5e7eb",
        padding: "24px",
      }}
    >
      {/* ================= HEADER ================= */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          marginBottom: 24,
        }}
      >
        <div style={{ fontSize: 42 }}>{data.flag}</div>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700 }}>{data.name}</h1>
          <div style={{ fontSize: 13, color: "#9ca3af" }}>
            Country political & economic overview
          </div>
        </div>
      </div>

      {/* ================= TOP GRID ================= */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "2fr 1fr",
          gap: 20,
          marginBottom: 24,
        }}
      >
        {/* ===== STOCK INDEX ===== */}
        <Card>
          <CardContent>
            <div style={{ fontSize: 13, color: "#9ca3af" }}>
              Stock index
            </div>
            <div style={{ fontSize: 22, fontWeight: 600 }}>
              {data.stockIndex}
            </div>
            <div
              style={{
                fontSize: 14,
                color: data.stockValue.startsWith("-")
                  ? "#ef4444"
                  : "#22c55e",
              }}
            >
              {data.stockValue}
            </div>
          </CardContent>
        </Card>

        {/* ===== BREAKING NEWS ===== */}
        <Card>
          <CardContent>
            <div
              style={{
                fontSize: 13,
                fontWeight: 600,
                marginBottom: 8,
              }}
            >
              📰 Breaking news
            </div>

            {data.news.length === 0 && (
              <div style={{ fontSize: 12, color: "#6b7280" }}>
                No recent news
              </div>
            )}

            {data.news.map((n, i) => (
              <div
                key={i}
                style={{
                  fontSize: 12,
                  marginBottom: 6,
                  paddingLeft: 8,
                  borderLeft: "2px solid #2563eb",
                }}
              >
                {n}
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* ================= PARLIAMENT ================= */}
      <Card style={{ marginBottom: 20 }}>
        <CardContent>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
            Parliament composition
          </div>
          <div style={{ fontSize: 13, color: "#9ca3af" }}>
            (visualization coming next)
          </div>

          <div
            style={{
              marginTop: 12,
              height: 120,
              background: "#020617",
              border: "1px dashed #334155",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#64748b",
              fontSize: 13,
            }}
          >
            Parliament chart placeholder
          </div>
        </CardContent>
      </Card>

      {/* ================= ELECTIONS / POLLS ================= */}
      <Card>
        <CardContent>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
            Elections & polls
          </div>
          <div style={{ fontSize: 13, color: "#9ca3af" }}>
            Latest polling & trends
          </div>

          <div
            style={{
              marginTop: 12,
              height: 120,
              background: "#020617",
              border: "1px dashed #334155",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#64748b",
              fontSize: 13,
            }}
          >
            Polling visualization placeholder
          </div>
        </CardContent>
      </Card>

      {/* ================= BACK ================= */}
      <div style={{ marginTop: 24 }}>
        <Button onClick={() => window.history.back()}>
          ← Back to map
        </Button>
      </div>
    </div>
  );
}
