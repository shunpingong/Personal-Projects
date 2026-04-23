interface MetricCardProps {
  label: string;
  value: string | number;
  detail: string;
  tone?: "neutral" | "accent" | "success" | "warning" | "critical";
}

export default function MetricCard({
  label,
  value,
  detail,
  tone = "neutral",
}: MetricCardProps) {
  return (
    <article className={`metric-card metric-card--${tone}`}>
      <p className="metric-card__label">{label}</p>
      <strong className="metric-card__value">{value}</strong>
      <span className="metric-card__detail">{detail}</span>
    </article>
  );
}
