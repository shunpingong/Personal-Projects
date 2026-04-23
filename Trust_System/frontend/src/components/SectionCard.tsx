import type { ReactNode } from "react";


interface SectionCardProps {
  title: string;
  eyebrow?: string;
  description?: string;
  children: ReactNode;
  actions?: ReactNode;
}

export default function SectionCard({
  title,
  eyebrow,
  description,
  children,
  actions,
}: SectionCardProps) {
  return (
    <section className="panel section-card">
      <header className="section-card__header">
        <div>
          {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
          <h3>{title}</h3>
          {description ? <p className="section-card__description">{description}</p> : null}
        </div>
        {actions ? <div className="section-card__actions">{actions}</div> : null}
      </header>
      {children}
    </section>
  );
}
