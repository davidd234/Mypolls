import { useEffect, useRef, useState } from "react";
import euMap from "../../assets/eu-map.svg?raw";

/* MOCK DATA – temporar, ușor de înlocuit cu API */
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
    container.innerHTML = euMap;
    const svg = container.querySelector("svg");

    svg.setAttribute("width", "100%");
    svg.setAttribute("height", "100%");
    svg.style.cursor = "grab";
    svg.style.background = "#0b0f14";

    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    while (svg.firstChild) g.appendChild(svg.firstChild);
    svg.appendChild(g);
    gRef.current = g;

    // CENTER ON LOAD
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

    // PAN
    svg.addEventListener("mousedown", (e) => {
      isPanning.current = true;
      lastPos.current = { x: e.clientX, y: e.clientY };
      svg.style.cursor = "grabbing";
    });

    window.addEventListener("mousemove", (e) => {
      if (!isPanning.current) return;
      setView((v) => ({
        ...v,
        x: v.x + (e.clientX - lastPos.current.x),
        y: v.y + (e.clientY - lastPos.current.y),
      }));
      lastPos.current = { x: e.clientX, y: e.clientY };
    });

    window.addEventListener("mouseup", () => {
      isPanning.current = false;
      svg.style.cursor = "grab";
    });

    // ZOOM (mouse centered)
    svg.addEventListener(
      "wheel",
      (e) => {
        e.preventDefault();
        const rect = svg.getBoundingClientRect();
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
      },
      { passive: false }
    );

    // COUNTRY CLICK = FOCUS + PANEL
    svg.querySelectorAll(".land").forEach((el) => {
      const code = el.id?.toLowerCase();
      el.style.fill = "#0f172a";
      el.style.stroke = "#2563eb";
      el.style.strokeWidth = "0.8";

      el.addEventListener("mouseenter", () => {
        el.style.fill = "#1e293b";
      });

      el.addEventListener("mouseleave", () => {
        el.style.fill = "#0f172a";
      });

      el.addEventListener("click", () => {
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
  }, []);

  useEffect(() => {
    if (!gRef.current) return;
    gRef.current.setAttribute(
      "transform",
      `translate(${view.x}, ${view.y}) scale(${view.scale})`
    );
  }, [view]);

  return (
    <div style={{ position: "relative", height: "100%" }}>
      <div
        ref={containerRef}
        style={{ width: "100%", height: "100%", overflow: "hidden" }}
      />

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
          }}
        >
          <strong>{selected.name}</strong>

          <div style={{ marginTop: 10 }}>
            <div>President:</div>
            <span style={{ color: selected.president?.color }}>
              {selected.president?.label}
            </span>
          </div>

          <div style={{ marginTop: 8 }}>
            <div>Government:</div>
            <span style={{ color: selected.government?.color }}>
              {selected.government?.label}
            </span>
          </div>

          <div style={{ marginTop: 8 }}>
            <div>AI alignment:</div>
            <span style={{ color: selected.ai?.color }}>
              {selected.ai?.label}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
