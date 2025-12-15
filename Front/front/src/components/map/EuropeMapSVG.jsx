import { useEffect, useRef, useState } from "react";
import euMap from "../../assets/eu-map.svg?raw";
import PoliticalLegend from "../legend/PoliticalLegend";
import { Button } from "../ui/button";
import { useNavigate } from "react-router-dom";

/* ================= DATA ================= */

const COUNTRY_INFO = {
  ro: {
    name: "Romania",
    president: { label: "EPP", color: "#1d4ed8" },
    government: { label: "EPP / S&D (mixed)", color: "#9ca3af" },
    ai: { label: "Pro-EU", color: "#7c3aed" },
  },
  fr: {
    name: "France",
    president: { label: "Renew", color: "#38bdf8" },
    government: { label: "Renew", color: "#38bdf8" },
    ai: { label: "Mixed", color: "#9ca3af" },
  },
  de: {
    name: "Germany",
    president: { label: "EPP", color: "#1d4ed8" },
    government: { label: "S&D / Greens", color: "#9ca3af" },
    ai: { label: "Pro-EU", color: "#7c3aed" },
  },
};

/* -1 = stânga | 0 = centru | +1 = dreapta */
const GOVERNMENT_IDEOLOGY = {
  ro: 0.2,
  fr: 0.1,
  de: -0.1,
  it: 0.7,
  es: -0.6,
  hu: 0.8,
  pt: -0.2,
};

// HELPER: Cele 5 culori fixe (cum ți-au plăcut)
const getIdeologyColor = (val) => {
  if (val === undefined) return "#1f2937";
  if (val <= -0.5) return "#b91c1c";       // Rosu Inchis
  if (val < -0.05) return "#ef4444";       // Rosu Deschis
  if (val >= -0.05 && val <= 0.05) return "#9ca3af"; // Gri
  if (val > 0.05 && val < 0.5) return "#60a5fa";     // Albastru Deschis
  return "#1d4ed8";                        // Albastru Inchis
};

export default function EuropeMapSVG() {
  const containerRef = useRef(null);
  const gRef = useRef(null);

  const [view, setView] = useState({ x: 0, y: 0, scale: 1 });
  const [initialView, setInitialView] = useState(null);
  const [selected, setSelected] = useState(null);
  const [mode, setMode] = useState("neutral");

  const isPanning = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });
const navigate = useNavigate();

  /* ================= INIT SVG & DRAG LOGIC ================= */

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.innerHTML = euMap;
    const svg = container.querySelector("svg");

    // Setări de bază SVG
    svg.setAttribute("width", "100%");
    svg.setAttribute("height", "100%");
    svg.style.background = "#0b0f14";
    svg.style.cursor = "grab";
    svg.style.display = "block"; // Fix pentru eventuale spatii
    svg.style.userSelect = "none"; // Vital pentru drag

    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    while (svg.firstChild) g.appendChild(svg.firstChild);
    svg.appendChild(g);
    gRef.current = g;

    // Centrare inițială
    requestAnimationFrame(() => {
      const bbox = g.getBBox();
      const rect = svg.getBoundingClientRect();
      const scale = 1.1;

      const v = {
        scale,
        x: rect.width / 2 - (bbox.x + bbox.width / 2) * scale,
        y: rect.height / 2 - (bbox.y + bbox.height / 2) * scale,
      };

      setView(v);
      setInitialView(v);
    });

    /* --- LOGICA DE DRAG REPARATĂ --- */
    // Definim funcțiile AICI, în interior, nu în render

    const onMouseDown = (e) => {
      e.preventDefault(); // ASTA ESTE CHEIA. Oprește browserul să "ia" imaginea.
      isPanning.current = true;
      lastPos.current = { x: e.clientX, y: e.clientY };
      svg.style.cursor = "grabbing";
    };

    const onMouseMove = (e) => {
      if (!isPanning.current) return;
      e.preventDefault();

      const dx = e.clientX - lastPos.current.x;
      const dy = e.clientY - lastPos.current.y;

      setView((v) => ({
        ...v,
        x: v.x + dx,
        y: v.y + dy,
      }));

      lastPos.current = { x: e.clientX, y: e.clientY };
    };

    const onMouseUp = () => {
      isPanning.current = false;
      svg.style.cursor = "grab";
    };

    // Atașăm ascultătorii direct pe elemente DOM (cel mai sigur mod)
    svg.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);

    /* HOVER + CLICK TARI */
    g.querySelectorAll(".land").forEach((el) => {
      const code = el.id?.toLowerCase();

      el.style.stroke = "#334155";
      el.style.strokeWidth = "0.5";
      el.style.cursor = "pointer";
      el.style.transition = "fill 0.2s ease";

      el.addEventListener("mouseenter", () => {
        el.style.filter = "brightness(1.2)";
        el.style.stroke = "#fff";
        el.style.strokeWidth = "1";
      });

      el.addEventListener("mouseleave", () => {
        el.style.filter = "none";
        el.style.stroke = "#334155";
        el.style.strokeWidth = "0.5";
      });

      el.addEventListener("click", (e) => {
        e.stopPropagation();
        const bbox = el.getBBox();
        const rect = svg.getBoundingClientRect();
        const scale = 2.5;

        setView({
          scale,
          x: rect.width / 2 - (bbox.x + bbox.width / 2) * scale,
          y: rect.height / 2 - (bbox.y + bbox.height / 2) * scale,
        });

        setSelected(COUNTRY_INFO[code] || { name: code?.toUpperCase() });
      });
    });

    // Cleanup la unmount
    return () => {
      svg.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, []);

  /* ================= TRANSFORM ================= */
  useEffect(() => {
    if (!gRef.current) return;
    gRef.current.setAttribute(
      "transform",
      `translate(${view.x}, ${view.y}) scale(${view.scale})`
    );
  }, [view]);

  /* ================= COLOR MODES ================= */
  useEffect(() => {
    if (!gRef.current) return;
    gRef.current.querySelectorAll(".land").forEach((el) => {
      const code = el.id?.toLowerCase();

      if (mode === "neutral") {
        el.style.fill = "#1e293b";
      } else if (mode === "ai") {
        el.style.fill = COUNTRY_INFO[code]?.ai?.color || "#1f2937";
      } else if (mode === "spectrum") {
        const v = GOVERNMENT_IDEOLOGY[code];
        el.style.fill = getIdeologyColor(v); // Cele 5 culori
      }
    });
  }, [mode]);

  /* ================= RENDER ================= */
  return (
    <div
      style={{ position: "relative", height: "100%", overflow: "hidden" }}
      // DOAR WHEEL AICI. MouseDown e gestionat de useEffect mai sus.
      onWheel={(e) => {
        e.preventDefault();
        const rect = e.currentTarget.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        setView((v) => {
          const factor = e.deltaY > 0 ? 0.9 : 1.1;
          const newScale = Math.min(Math.max(v.scale * factor, 0.6), 8);
          const ratio = newScale / v.scale;
          return {
            scale: newScale,
            x: mx - ratio * (mx - v.x),
            y: my - ratio * (my - v.y),
          };
        });
      }}
    >
      <div ref={containerRef} style={{ width: "100%", height: "100%" }} />

      {/* CONTROLS */}
      <div style={{ position: "absolute", top: 12, left: 12, display: "flex", gap: 8, zIndex: 10 }}>
        <Button onClick={() => setMode("neutral")} variant={mode === "neutral" ? "default" : "secondary"}>Neutral</Button>
        <Button onClick={() => setMode("spectrum")} variant={mode === "spectrum" ? "default" : "secondary"}>Left ↔ Right</Button>
        <Button onClick={() => setMode("ai")} variant={mode === "ai" ? "default" : "secondary"}>AI Stance</Button>
        <Button onClick={() => initialView && setView(initialView)} variant="outline">Reset View</Button>
      </div>

      {/* LEGENDA BARA (Fixe, 5 culori) */}
      {mode === "spectrum" && (
        <div
          style={{
            position: "absolute",
            bottom: 30,
            left: "50%",
            transform: "translateX(-50%)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 5,
            pointerEvents: "none"
          }}
        >
          <div style={{ display: "flex", borderRadius: 4, overflow: "hidden", border: "1px solid #374151" }}>
            <div style={{ width: 60, height: 12, background: "#b91c1c" }}></div>
            <div style={{ width: 60, height: 12, background: "#ef4444" }}></div>
            <div style={{ width: 60, height: 12, background: "#9ca3af" }}></div>
            <div style={{ width: 60, height: 12, background: "#60a5fa" }}></div>
            <div style={{ width: 60, height: 12, background: "#1d4ed8" }}></div>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", width: "100%", fontSize: 10, color: "#9ca3af", fontWeight: "bold" }}>
            <span>LEFT</span>
            <span>CENTER</span>
            <span>RIGHT</span>
          </div>
        </div>
      )}

      {/* INFO BOX */}
      {selected && (
  <div
    style={{
      position: "absolute",
      top: 60,
      right: 20,
      width: 280,
      background: "rgba(15, 23, 42, 0.95)",
      backdropFilter: "blur(6px)",
      border: "1px solid #334155",
      borderRadius: "8px",
      padding: 16,
      fontSize: 13,
      color: "#e2e8f0",
      zIndex: 20,
      boxShadow: "0 10px 25px rgba(0,0,0,0.6)",
    }}
  >
    {/* HEADER */}
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: 10,
      }}
    >
      <strong style={{ fontSize: 16 }}>{selected.name}</strong>
      <button
        onClick={() => setSelected(null)}
        style={{
          background: "transparent",
          border: "none",
          color: "#94a3b8",
          cursor: "pointer",
          fontSize: 14,
        }}
      >
        ✕
      </button>
    </div>

    {/* INFO */}
    <div style={{ marginBottom: 6 }}>
      President:{" "}
      <span style={{ color: selected.president?.color, fontWeight: 500 }}>
        {selected.president?.label || "N/A"}
      </span>
    </div>

    <div style={{ marginBottom: 6 }}>
      Government:{" "}
      <span style={{ color: selected.government?.color, fontWeight: 500 }}>
        {selected.government?.label || "N/A"}
      </span>
    </div>

    <div style={{ marginBottom: 12 }}>
      AI Stance:{" "}
      <span style={{ color: selected.ai?.color, fontWeight: 500 }}>
        {selected.ai?.label || "N/A"}
      </span>
    </div>

    {/* CTA BUTTON */}
    <button
      onClick={() =>
        navigate(`/country/${selected.name.toLowerCase().slice(0, 2)}`)
      }
      style={{
        width: "100%",
        padding: "10px 12px",
        background:
          "linear-gradient(135deg, #2563eb 0%, #1e40af 100%)",
        border: "none",
        borderRadius: 6,
        color: "#fff",
        fontWeight: 600,
        cursor: "pointer",
        letterSpacing: "0.3px",
        boxShadow: "0 4px 10px rgba(37,99,235,0.4)",
      }}
    >
      View country details →
    </button>
  </div>
)}


      <PoliticalLegend />
    </div>
  );
}