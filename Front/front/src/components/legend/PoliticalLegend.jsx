export default function PoliticalLegend() {
  return (
    <div
      style={{
        position: "absolute",
        right: 16,
        bottom: 16,
        width: 280,
        background: "#0e1116",
        border: "1px solid #1f2937",
        padding: 14,
        fontSize: 12,
        lineHeight: 1.4,
      }}
    >
      {/* EU PARLIAMENT GROUPS */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontWeight: 600, marginBottom: 6 }}>
          🇪🇺 European Parliament Groups
        </div>

        <LegendRow color="#0b1f3a" label="ID / ECR / ESN / PfE" />
        <LegendRow color="#1d4ed8" label="EPP" />
        <LegendRow color="#38bdf8" label="Renew" />
        <LegendRow color="#b91c1c" label="S&D (Socialists)" />
        <LegendRow color="#15803d" label="Greens / EFA" />
        <LegendRow color="#7f1d1d" label="The Left" />
      </div>

      {/* AI ALIGNMENT */}
      <div>
        <div style={{ fontWeight: 600, marginBottom: 6 }}>
          🤖 AI Alignment
        </div>

        <LegendRow color="#7c3aed" label="Pro-EU" />
        <LegendRow color="#9ca3af" label="Mixed" />
        <LegendRow color="#ea580c" label="Anti-EU" />
      </div>
    </div>
  );
}

function LegendRow({ color, label }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        marginBottom: 4,
      }}
    >
      <span
        style={{
          width: 12,
          height: 12,
          background: color,
          display: "inline-block",
          marginRight: 8,
        }}
      />
      <span>{label}</span>
    </div>
  );
}
