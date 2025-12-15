import { useEffect, useRef, useState } from "react";
import euMap from "../../assets/eu-map.svg?raw";
import PoliticalLegend from "../legend/PoliticalLegend";

/* MOCK DATA */
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

export default function EuropeMapSVG() {
  const containerRef = useRef(null);
  const gRef = useRef(null);

  const [view, setView] = useState({ x: 0, y: 0, scale: 1 });
  const [selected, setSelected] = useState(null);

  const isPanning = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.innerHTML = euMap;
    const svg = container.querySelector("svg");
    if (!svg) return;

    svg.setAttribute("width", "100%");
    svg.setAttribute("height", "100%");
    svg.style.background = "#0b0f14";
    svg.style.cursor = "grab";

    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    while (svg.firstChild) g.appendChild(svg.firstChild);
    svg.appendChild(g);
    gRef.current = g;

    /* CENTER ON LOAD */
    requestAnimationFrame(() => {
      const bbox = g.getBBox();
      const rect = svg.getBoundingClientRect();
      const scale = 1.1;

      setView({
        scale,
        x: rect.width / 2 - (bbox.x + bbox.width / 2) * scale,
        y: rect.height / 2 - (bbox.y + bbox.height / 2) * scale,
      });
    });

    /* COUNTRY STYLE + CLICK */
    svg.querySelectorAll(".land").forEach((el) => {
      const code = el.id?.toLowerCase();

      el.style.fill = "#0f172a";
      el.style.stroke = "#2563eb";
      el.style.strokeWidth = "0.8";
      el.style.cursor = "pointer";

      el.addEventListener("mouseenter", () => {
        el.style.fill = "#1e293b";
      });

      el.addEventListener("mouseleave", () => {
        el.style.fill = "#0f172a";
      });

      el.addEventListener("click", (e) => {
        // Opțional: prevenim click-ul dacă tocmai am făcut drag (mic detaliu UX)
        e.stopPropagation();

        const bbox = el.getBBox();
        const rect = svg.getBoundingClientRect();
        const scale = 2.2;

        setView({
          scale,
          x: rect.width / 2 - (bbox.x + bbox.width / 2) * scale,
          y: rect.height / 2 - (bbox.y + bbox.height / 2) * scale,
        });

        setSelected(COUNTRY_INFO[code] || { name: code.toUpperCase() });
      });
    });

    /* --- FIX START: PAN LOGIC --- */

    // 1. Mousedown direct pe SVG (nu prin React prop)
    const onMouseDown = (e) => {
      e.preventDefault(); // CRITIC: Oprește browserul să selecteze/traga SVG-ul ca imagine
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

    // Atașăm mousedown direct de elementul SVG creat manual
    svg.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);

    return () => {
      svg.removeEventListener("mousedown", onMouseDown); // Cleanup
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
    /* --- FIX END --- */

  }, []);

  /* APPLY TRANSFORM */
  useEffect(() => {
    if (!gRef.current) return;
    gRef.current.setAttribute(
      "transform",
      `translate(${view.x}, ${view.y}) scale(${view.scale})`
    );
  }, [view]);

  return (
    <div
      style={{ position: "relative", height: "100%" }}
      // onMouseDown a fost scos de aici și mutat în useEffect
      onWheel={(e) => {
        e.preventDefault();
        const rect = e.currentTarget.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        setView((v) => {
          const factor = e.deltaY > 0 ? 0.9 : 1.1;
          const newScale = Math.min(Math.max(v.scale * factor, 0.6), 4);
          const ratio = newScale / v.scale;

          return {
            scale: newScale,
            x: mx - ratio * (mx - v.x),
            y: my - ratio * (my - v.y),
          };
        });
      }}
    >
      <div
        ref={containerRef}
        style={{ width: "100%", height: "100%", overflow: "hidden" }}
      />

      <PoliticalLegend />

      {selected && (
        <div
          style={{
            position: "absolute",
            top: 20,
            right: 20,
            width: 260,
            background: "#0e1116",
            border: "1px solid #1f2937",
            padding: 16,
            fontSize: 13,
            pointerEvents: "none" // Ca să nu interfereze cu drag-ul dacă dai click pe tooltip
          }}
        >
          <strong>{selected.name}</strong>

          <div style={{ marginTop: 10 }}>
            President:
            <span style={{ color: selected.president?.color, marginLeft: 6 }}>
              {selected.president?.label}
            </span>
          </div>

          <div style={{ marginTop: 8 }}>
            Government:
            <span style={{ color: selected.government?.color, marginLeft: 6 }}>
              {selected.government?.label}
            </span>
          </div>

          <div style={{ marginTop: 8 }}>
            AI alignment:
            <span style={{ color: selected.ai?.color, marginLeft: 6 }}>
              {selected.ai?.label}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}