import React from "react";

interface Props {
  title:    string;
  subtitle?: string;
  icon?:    React.ReactNode;
  action?:  React.ReactNode;
}

export default function SectionHeader({ title, subtitle, icon, action }: Props) {
  return (
    <div style={s.header}>
      <div style={s.left}>
        {icon && <div style={s.icon}>{icon}</div>}
        <div>
          <h1 style={s.title}>{title}</h1>
          {subtitle && <p style={s.subtitle}>{subtitle}</p>}
        </div>
      </div>
      {action && <div style={s.action}>{action}</div>}
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  header:   { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px", paddingBottom: "16px", borderBottom: "1px solid #2A2F38" },
  left:     { display: "flex", alignItems: "center", gap: "12px" },
  icon:     { flexShrink: 0 },
  title:    { color: "#E8EAF0", fontSize: "20px", fontWeight: "700", fontFamily: "'Rajdhani', sans-serif", letterSpacing: "0.04em", lineHeight: 1 },
  subtitle: { color: "#8A929E", fontSize: "12px", marginTop: "4px" },
  action:   { flexShrink: 0 },
};
