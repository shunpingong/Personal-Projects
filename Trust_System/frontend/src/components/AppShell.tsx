import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../app/App";
import StatusPill from "./StatusPill";


interface NavItem {
  to: string;
  label: string;
  roles?: Array<"admin" | "moderator" | "user">;
}

const navigation: NavItem[] = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/reports", label: "Reports" },
  { to: "/users", label: "Users", roles: ["admin", "moderator"] },
  { to: "/incidents", label: "Incidents", roles: ["admin", "moderator"] },
  { to: "/audit-logs", label: "Audit Logs", roles: ["admin", "moderator"] },
];

export default function AppShell() {
  const { user, logout } = useAuth();

  if (!user) {
    return null;
  }

  const links = navigation.filter((item) => !item.roles || item.roles.includes(user.role));

  return (
    <div className="app-shell">
      <aside className="sidebar panel">
        <div className="brand-block">
          <p className="eyebrow">Trust & Safety</p>
          <h1>Trust System</h1>
          <p className="sidebar-copy">
            Operational workspace for moderation queues, identity controls, and incident escalation.
          </p>
        </div>

        <nav className="sidebar-nav" aria-label="Primary navigation">
          {links.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                isActive ? "sidebar-link sidebar-link--active" : "sidebar-link"
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <p className="sidebar-footer__label">Signed in as</p>
          <strong>{user.full_name}</strong>
          <span>{user.email}</span>
          <StatusPill value={user.role} variant="role" />
          <button type="button" className="button button--ghost" onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Live environment</p>
            <h2>Shared operational dashboard</h2>
          </div>
          <div className="topbar-status">
            <StatusPill value={user.is_active ? "active" : "inactive"} variant="state" />
            <span>{user.role} access</span>
          </div>
        </header>

        <Outlet />
      </main>
    </div>
  );
}
