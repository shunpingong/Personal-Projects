import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "../app/App";
import SectionCard from "../components/SectionCard";
import StatusPill from "../components/StatusPill";
import { ApiError, usersApi } from "../services/api";
import type { UserRole } from "../types/api";


export default function UsersPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("user");
  const [isActive, setIsActive] = useState(true);
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);

  const canViewUsers = user?.role === "admin" || user?.role === "moderator";
  const isAdmin = user?.role === "admin";

  const usersQuery = useQuery({
    queryKey: ["users", "list"],
    queryFn: () => usersApi.list(100, 0),
    enabled: canViewUsers,
  });

  const createUserMutation = useMutation({
    mutationFn: usersApi.create,
    onSuccess: () => {
      setEmail("");
      setFullName("");
      setPassword("");
      setRole("user");
      setIsActive(true);
      setFormError(null);
      setFormSuccess("User created successfully.");
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (error) => {
      setFormSuccess(null);
      setFormError(error instanceof ApiError ? error.message : "Unable to create the user.");
    },
  });

  const updateUserMutation = useMutation({
    mutationFn: ({ userId, nextIsActive }: { userId: string; nextIsActive: boolean }) =>
      usersApi.update(userId, { is_active: nextIsActive }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });

  if (!canViewUsers) {
    return (
      <div className="page-grid">
        <SectionCard
          title="User administration"
          eyebrow="Users"
          description="Only moderators and admins can inspect or manage user accounts."
        >
          <p className="empty-copy">
            Your current role does not include access to the user directory.
          </p>
        </SectionCard>
      </div>
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await createUserMutation.mutateAsync({
      email,
      full_name: fullName,
      password,
      role,
      is_active: isActive,
    });
  }

  return (
    <div className="page-grid">
      {isAdmin ? (
        <SectionCard
          title="Create account"
          eyebrow="Users"
          description="Provision a new account directly from the admin workspace."
        >
          <form className="form-grid" onSubmit={handleSubmit}>
            <label className="field">
              <span>Full name</span>
              <input
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                required
              />
            </label>

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

            <label className="field">
              <span>Role</span>
              <select value={role} onChange={(event) => setRole(event.target.value as UserRole)}>
                <option value="user">user</option>
                <option value="moderator">moderator</option>
                <option value="admin">admin</option>
              </select>
            </label>

            <label className="field field--checkbox">
              <input
                type="checkbox"
                checked={isActive}
                onChange={(event) => setIsActive(event.target.checked)}
              />
              <span>Mark account as active on creation</span>
            </label>

            {formSuccess ? <p className="form-success">{formSuccess}</p> : null}
            {formError ? <p className="form-error">{formError}</p> : null}

            <button
              type="submit"
              className="button button--primary"
              disabled={createUserMutation.isPending}
            >
              {createUserMutation.isPending ? "Creating..." : "Create user"}
            </button>
          </form>
        </SectionCard>
      ) : null}

      <SectionCard
        title="User directory"
        eyebrow="Users"
        description="Live account inventory from the FastAPI service."
      >
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created</th>
                <th>Admin action</th>
              </tr>
            </thead>
            <tbody>
              {(usersQuery.data ?? []).map((entry) => (
                <tr key={entry.id}>
                  <td>{entry.full_name}</td>
                  <td>{entry.email}</td>
                  <td>
                    <StatusPill value={entry.role} variant="role" />
                  </td>
                  <td>
                    <StatusPill value={entry.is_active ? "active" : "inactive"} variant="state" />
                  </td>
                  <td>{new Date(entry.created_at).toLocaleString()}</td>
                  <td>
                    {isAdmin ? (
                      <button
                        type="button"
                        className="button button--ghost"
                        onClick={() =>
                          updateUserMutation.mutate({
                            userId: entry.id,
                            nextIsActive: !entry.is_active,
                          })
                        }
                        disabled={updateUserMutation.isPending}
                      >
                        {entry.is_active ? "Disable" : "Enable"}
                      </button>
                    ) : (
                      <span className="muted-copy">View only</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </div>
  );
}
