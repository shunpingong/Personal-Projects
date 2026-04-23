import { FormEvent, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../app/App";
import { ApiError } from "../services/api";


export default function LoginPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("admin@trustsystem.dev");
  const [password, setPassword] = useState("AdminPassword123!");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      await auth.login({ email, password });
      const redirectTarget = (location.state as { from?: string } | null)?.from ?? "/dashboard";
      navigate(redirectTarget, { replace: true });
    } catch (caughtError) {
      setError(
        caughtError instanceof ApiError ? caughtError.message : "Unable to sign in right now."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="auth-layout">
      <div className="auth-card">
        <p className="eyebrow">Trust System</p>
        <h1>Operational sign in</h1>
        <p className="auth-card__copy">
          Access moderation queues, user administration, derived incidents, and the audit view from
          one workspace.
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>

          <label className="field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>

          {error ? <p className="form-error">{error}</p> : null}

          <button type="submit" className="button button--primary" disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="auth-note">
          <strong>Bootstrap admin</strong>
          <span>admin@trustsystem.dev</span>
          <span>AdminPassword123!</span>
        </div>
      </div>
    </div>
  );
}
