import React from "react";

interface Props {
  icon:      React.ReactNode;
  label:     string;
  value:     string;
  detail?:   string;
  barValue?: number;   // 0–100
  barColor?: string;
}

export default function StatCard({ icon, label, value, detail, barValue, barColor = "#F58C1F" }: Props) {
  return (
    <div style={s.card}>
      <div style={s.header}>
        <div style={s.iconWrap}>{icon}</div>
        <span style={s.label}>{label}</span>
      </div>

      <div style={s.value}>{value}</div>

      {detail && <div style={s.detail}>{detail}</div>}

      {barValue !== undefined && (
        <div style={s.barTrack}>
          <div style={{
            ...s.barFill,
            width: `${Math.min(100, Math.max(0, barValue))}%`,
            backgroundColor: barColor,
          }} />
        </div>
      )}
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  card:    { backgroundColor: "#161A1F", border: "1px solid #2A2F38", borderRadius: "8px", padding: "16px" },
  header:  { display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" },
  iconWrap:{ flexShrink: 0 },
  label:   { color: "#8A929E", fontSize: "11px", fontWeight: "600", letterSpacing: "0.08em", textTransform: "uppercase" },
  value:   { color: "#E8EAF0", fontSize: "26px", fontWeight: "700", fontFamily: "'Rajdhani', sans-serif", lineHeight: 1, marginBottom: "4px" },
  detail:  { color: "#4A515C", fontSize: "11px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", marginBottom: "10px" },
  barTrack:{ height: "3px", backgroundColor: "#2A2F38", borderRadius: "2px", overflow: "hidden" },
  barFill: { height: "100%", borderRadius: "2px", transition: "width 0.4s ease" },
};
