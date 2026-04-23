interface StatusPillProps {
  value: string;
  variant?: "status" | "role" | "severity" | "state" | "tone";
}

function toneClass(value: string, variant: StatusPillProps["variant"]): string {
  const normalized = value.toLowerCase();

  if (variant === "role") {
    if (normalized === "admin") return "pill--critical";
    if (normalized === "moderator") return "pill--warning";
    return "pill--neutral";
  }

  if (variant === "severity") {
    if (normalized === "critical") return "pill--critical";
    if (normalized === "high") return "pill--warning";
    return "pill--neutral";
  }

  if (variant === "state") {
    return normalized === "active" ? "pill--success" : "pill--neutral";
  }

  if (normalized === "reviewed" || normalized === "success") return "pill--success";
  if (normalized === "escalated" || normalized === "critical") return "pill--critical";
  if (normalized === "pending" || normalized === "warning") return "pill--warning";
  return "pill--neutral";
}

export default function StatusPill({ value, variant = "status" }: StatusPillProps) {
  return <span className={`pill ${toneClass(value, variant)}`}>{value}</span>;
}
