"use client";

type ErrorPageProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  return (
    <main className="pageShell">
      <section className="panel panelHero">
        <p className="eyebrow">Frontend Error</p>
        <h1>Something broke in the UI shell.</h1>
        <p>{error.message}</p>
        <button className="primaryButton" onClick={reset}>
          Retry
        </button>
      </section>
    </main>
  );
}

