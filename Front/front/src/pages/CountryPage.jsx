// src/pages/CountryPage.jsx
// Replace your current file with this version to enable the "Recent news" card.
// News source: GDELT DOC 2.0 API (CORS enabled), mode=artlist, format=json.

import { useParams } from "react-router-dom";
import { useState, useEffect, useMemo, useCallback } from "react";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";

function parseGdeltDate(s) {
  // GDELT often returns seendate like: YYYYMMDDHHMMSS
  if (!s || typeof s !== "string") return null;

  // Already ISO-ish?
  const isoLike = Date.parse(s);
  if (!Number.isNaN(isoLike)) return new Date(isoLike);

  const m = s.match(/^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})$/);
  if (!m) return null;

  const [, yy, mm, dd, hh, mi, ss] = m;
  // Treat as UTC (safe enough for a headline list)
  return new Date(`${yy}-${mm}-${dd}T${hh}:${mi}:${ss}Z`);
}

function buildGdeltUrl(countryName) {
  const u = new URL("https://api.gdeltproject.org/api/v2/doc/doc");

  // Keep results readable: English-only sources.
  // (You can remove `sourcelang:english` if you want multilingual results.)
  u.searchParams.set("query", `\"${countryName}\" sourcelang:english`);

  u.searchParams.set("mode", "artlist");
  u.searchParams.set("format", "json");
  u.searchParams.set("sort", "datedesc");
  u.searchParams.set("maxrecords", "8");
  u.searchParams.set("timespan", "3d");

  return u.toString();
}

export default function CountryPage() {
  const { code } = useParams();

  // ================= STOCK =================
  const [stockData, setStockData] = useState(null);
  const [pageLoading, setPageLoading] = useState(true);
  const [stockError, setStockError] = useState(null);

  // ================= NEWS =================
  const [news, setNews] = useState([]);
  const [newsLoading, setNewsLoading] = useState(true);
  const [newsError, setNewsError] = useState(null);
  const [newsNonce, setNewsNonce] = useState(0);

  const countryNames = useMemo(
    () => ({
      ro: "Romania 🇷🇴",
      fr: "France 🇫🇷",
      de: "Germany 🇩🇪",
      at: "Austria 🇦🇹",
      be: "Belgium 🇧🇪",
      bg: "Bulgaria 🇧🇬",
      hr: "Croatia 🇭🇷",
      cy: "Cyprus 🇨🇾",
      cz: "Czech Republic 🇨🇿",
      dk: "Denmark 🇩🇰",
      ee: "Estonia 🇪🇪",
      fi: "Finland 🇫🇮",
      gr: "Greece 🇬🇷",
      hu: "Hungary 🇭🇺",
      ie: "Ireland 🇮🇪",
      it: "Italy 🇮🇹",
      lv: "Latvia 🇱🇻",
      lt: "Lithuania 🇱🇹",
      lu: "Luxembourg 🇱🇺",
      mt: "Malta 🇲🇹",
      nl: "Netherlands 🇳🇱",
      pl: "Poland 🇵🇱",
      pt: "Portugal 🇵🇹",
      sk: "Slovakia 🇸🇰",
      si: "Slovenia 🇸🇮",
      es: "Spain 🇪🇸",
      se: "Sweden 🇸🇪",
    }),
    []
  );

  const countryLabel = countryNames[code] || `${code?.toUpperCase()} 🏳️`;

  // Fix for multi-word names (Czech Republic, etc.): last token = flag, rest = name
  const countryParts = countryLabel.split(" ");
  const countryFlag = countryParts[countryParts.length - 1];
  const countryDisplayName = countryParts.slice(0, -1).join(" ");

  // Fetch real stock data from API
  useEffect(() => {
    if (!code) return;

    setPageLoading(true);
    setStockError(null);

    fetch(`http://localhost:8000/api/country/${code.toUpperCase()}/stock`)
      .then((res) => res.json())
      .then((data) => {
        setStockData(data);
        setPageLoading(false);
      })
      .catch((err) => {
        console.error("Stock fetch error:", err);
        setStockError("No stock data available");
        setPageLoading(false);
      });
  }, [code]);

  const fetchNews = useCallback(
    (signal) => {
      if (!countryDisplayName) return Promise.resolve();

      setNewsLoading(true);
      setNewsError(null);

      return fetch(buildGdeltUrl(countryDisplayName), { signal })
        .then((res) => {
          if (!res.ok) throw new Error(`News HTTP ${res.status}`);
          return res.json();
        })
        .then((data) => {
          const articles = Array.isArray(data?.articles) ? data.articles : [];
          setNews(articles);
        })
        .catch((err) => {
          if (err?.name === "AbortError") return;
          console.error("News fetch error:", err);
          setNewsError("News unavailable (rate-limit or network)");
          setNews([]);
        })
        .finally(() => setNewsLoading(false));
    },
    [countryDisplayName]
  );

  // Fetch news from GDELT (client-side, CORS enabled)
  useEffect(() => {
    const controller = new AbortController();
    fetchNews(controller.signal);
    return () => controller.abort();
  }, [fetchNews, newsNonce]);

  if (pageLoading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          background: "#0b0f14",
          color: "#e5e7eb",
          padding: "24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div style={{ fontSize: 18, color: "#9ca3af" }}>
          Loading {countryLabel} data...
        </div>
      </div>
    );
  }

  const changePercent = stockData?.change_percent ?? 0;
  const hasStockData = stockData && !stockData.error && stockData.status === "ok";

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
        <div style={{ fontSize: 42 }}>{countryFlag}</div>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700 }}>{countryDisplayName}</h1>
          <div style={{ fontSize: 13, color: "#9ca3af" }}>
            Live political & economic overview
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
        {/* ===== LIVE STOCK INDEX ===== */}
        <Card>
          <CardContent style={{ padding: "24px" }}>
            <div style={{ fontSize: 13, color: "#9ca3af", marginBottom: 8 }}>
              Stock market (live)
            </div>
            {hasStockData ? (
              <>
                <div style={{ fontSize: 22, fontWeight: 600, marginBottom: 4 }}>
                  {stockData.index}
                </div>
                <div style={{ fontSize: 36, fontWeight: 800, marginBottom: 8 }}>
                  {stockData.value?.toLocaleString() || "N/A"}
                </div>
                <div
                  style={{
                    fontSize: 20,
                    fontWeight: 700,
                    color: changePercent >= 0 ? "#22c55e" : "#ef4444",
                  }}
                >
                  {changePercent >= 0 ? "+" : ""}
                  {changePercent.toFixed(2)}%
                </div>
                <p style={{ fontSize: 12, opacity: 0.8, marginTop: 12 }}>
                  Source: {stockData.source?.split("/")[2]} •{" "}
                  {new Date(stockData.updated_at).toLocaleString()}
                </p>
              </>
            ) : (
              <div style={{ color: "#9ca3af", fontSize: 16 }}>
                {stockError || "No stock data available"}
              </div>
            )}
          </CardContent>
        </Card>

        {/* ===== NEWS (GDELT) ===== */}
        <Card>
          <CardContent style={{ padding: "24px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  marginBottom: 12,
                }}
              >
                📰 Recent news
              </div>

              <button
                onClick={() => setNewsNonce((x) => x + 1)}
                style={{
                  background: "transparent",
                  border: "1px solid #334155",
                  borderRadius: 6,
                  padding: "6px 10px",
                  color: "#cbd5e1",
                  cursor: "pointer",
                  fontSize: 12,
                }}
                title="Refresh"
              >
                ↻
              </button>
            </div>

            {newsLoading && (
              <div style={{ fontSize: 12, color: "#6b7280" }}>Loading news…</div>
            )}

            {!newsLoading && newsError && (
              <div style={{ fontSize: 12, color: "#fca5a5" }}>
                {newsError}
              </div>
            )}

            {!newsLoading && !newsError && news.length === 0 && (
              <div style={{ fontSize: 12, color: "#6b7280" }}>No recent headlines</div>
            )}

            {!newsLoading && !newsError && news.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {news.slice(0, 8).map((a, i) => {
                  const dt = parseGdeltDate(a?.seendate);
                  const domain = a?.domain || (a?.url ? new URL(a.url).hostname : "");

                  return (
                    <a
                      key={`${a?.url || i}`}
                      href={a?.url}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        textDecoration: "none",
                        color: "inherit",
                        paddingLeft: 10,
                        borderLeft: "2px solid #2563eb",
                      }}
                    >
                      <div style={{ fontSize: 12, lineHeight: 1.35, fontWeight: 600 }}>
                        {a?.title || "Untitled"}
                      </div>
                      <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 2 }}>
                        {domain}
                        {dt ? ` • ${dt.toLocaleString()}` : ""}
                      </div>
                    </a>
                  );
                })}
              </div>
            )}

            <div style={{ marginTop: 12, fontSize: 11, color: "#64748b" }}>
              Source: GDELT DOC 2.0
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ================= ML PREDICTIONS ================= */}
      <Card style={{ marginBottom: 20 }}>
        <CardContent style={{ padding: "24px" }}>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
            ML Election Predictions
          </div>
          <div style={{ fontSize: 13, color: "#9ca3af" }}>
            Party vote shares (model forecast)
          </div>
          <div
            style={{
              marginTop: 16,
              height: 160,
              background: "#020617",
              border: "1px dashed #334155",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#64748b",
              fontSize: 13,
              borderRadius: 8,
            }}
          >
            Predictions chart (connect /api/pmb/2024)
          </div>
        </CardContent>
      </Card>

      {/* ================= STOCK SIGNAL ================= */}
      {hasStockData && changePercent < -0.5 && (
        <div
          style={{
            padding: "20px",
            background: "linear-gradient(135deg, #fef3c7, #fde68a)",
            borderLeft: "5px solid #f59e0b",
            borderRadius: "8px",
            marginBottom: 20,
          }}
        >
          <div
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: "#92400e",
              marginBottom: 4,
            }}
          >
            📉 Market Signal
          </div>
          <div style={{ fontSize: 13, color: "#92400e" }}>
            Stock decline ({changePercent.toFixed(2)}%) may predict stronger
            populist/right-wing support.
          </div>
        </div>
      )}

      {/* ================= BACK BUTTON ================= */}
      <div style={{ marginTop: 24 }}>
        <Button
          onClick={() => window.history.back()}
          style={{
            background: "#2563eb",
            color: "white",
            padding: "12px 24px",
            borderRadius: 8,
          }}
        >
          ← Back to Europe map
        </Button>
      </div>
    </div>
  );
}
