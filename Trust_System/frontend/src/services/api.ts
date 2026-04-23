import {
  clearSessionTokens,
  getAccessToken,
  getRefreshToken,
  setSessionTokens,
  signalAuthExpiry,
} from "./session";
import type {
  CreateReportPayload,
  CreateUserPayload,
  Incident,
  LoginPayload,
  RegisterPayload,
  Report,
  ReportStatus,
  TokenPair,
  UpdateUserPayload,
  User,
} from "../types/api";


const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "/api/v1").replace(/\/$/, "");

type Primitive = string | number | boolean;

interface ApiRequestInit extends Omit<RequestInit, "body"> {
  auth?: boolean;
  body?: BodyInit | object | null;
}

export class ApiError extends Error {
  status: number;
  payload?: unknown;

  constructor(status: number, message: string, payload?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

function createUrl(path: string): string {
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

function isJsonBody(body: ApiRequestInit["body"]): body is object {
  return Boolean(
    body &&
      typeof body === "object" &&
      !(body instanceof FormData) &&
      !(body instanceof URLSearchParams) &&
      !(body instanceof Blob) &&
      !(body instanceof ArrayBuffer)
  );
}

async function parseResponsePayload(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

function buildError(response: Response, payload: unknown): ApiError {
  if (
    payload &&
    typeof payload === "object" &&
    "detail" in payload &&
    typeof payload.detail === "string"
  ) {
    return new ApiError(response.status, payload.detail, payload);
  }

  if (typeof payload === "string" && payload.trim().length > 0) {
    return new ApiError(response.status, payload, payload);
  }

  return new ApiError(response.status, response.statusText || "Request failed", payload);
}

async function rawRequest<T>(
  path: string,
  init: ApiRequestInit = {},
  allowRefresh = true
): Promise<T> {
  const headers = new Headers(init.headers);

  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  let body: BodyInit | null | undefined;

  if (isJsonBody(init.body)) {
    body = JSON.stringify(init.body);
    if (!headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
  } else {
    body = init.body as BodyInit | null | undefined;
  }

  if (init.auth !== false) {
    const accessToken = getAccessToken();
    if (accessToken) {
      headers.set("Authorization", `Bearer ${accessToken}`);
    }
  }

  const response = await fetch(createUrl(path), {
    ...init,
    headers,
    body,
  });
  const payload = await parseResponsePayload(response);

  if (response.status === 401 && init.auth !== false && allowRefresh) {
    const refreshed = await refreshTokens();
    if (refreshed) {
      return rawRequest<T>(path, init, false);
    }

    signalAuthExpiry();
  }

  if (!response.ok) {
    throw buildError(response, payload);
  }

  return payload as T;
}

async function refreshTokens(): Promise<boolean> {
  const refreshToken = getRefreshToken();

  if (!refreshToken) {
    return false;
  }

  try {
    const tokens = await rawRequest<TokenPair>(
      "/auth/refresh",
      {
        auth: false,
        method: "POST",
        body: {
          refresh_token: refreshToken,
        },
      },
      false
    );

    setSessionTokens(tokens);
    return true;
  } catch {
    clearSessionTokens();
    return false;
  }
}

function buildSearch(params?: Record<string, Primitive | null | undefined>): string {
  if (!params) {
    return "";
  }

  const searchParams = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && `${value}`.length > 0) {
      searchParams.set(key, `${value}`);
    }
  }

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export const authApi = {
  async login(payload: LoginPayload): Promise<TokenPair> {
    return rawRequest<TokenPair>("/auth/login", {
      auth: false,
      method: "POST",
      body: payload,
    });
  },

  async register(payload: RegisterPayload): Promise<User> {
    return rawRequest<User>("/auth/register", {
      auth: false,
      method: "POST",
      body: payload,
    });
  },

  async me(): Promise<User> {
    return rawRequest<User>("/auth/me");
  },
};

export const usersApi = {
  async list(limit = 50, offset = 0): Promise<User[]> {
    return rawRequest<User[]>(`/users${buildSearch({ limit, offset })}`);
  },

  async create(payload: CreateUserPayload): Promise<User> {
    return rawRequest<User>("/users", {
      method: "POST",
      body: payload,
    });
  },

  async update(userId: string, payload: UpdateUserPayload): Promise<User> {
    return rawRequest<User>(`/users/${userId}`, {
      method: "PATCH",
      body: payload,
    });
  },
};

export const reportsApi = {
  async list(options?: {
    status?: ReportStatus | "all";
    limit?: number;
    offset?: number;
  }): Promise<Report[]> {
    const { status, limit = 50, offset = 0 } = options ?? {};
    return rawRequest<Report[]>(
      `/reports${buildSearch({
        status: status && status !== "all" ? status : undefined,
        limit,
        offset,
      })}`
    );
  },

  async create(payload: CreateReportPayload): Promise<Report> {
    return rawRequest<Report>("/reports", {
      method: "POST",
      body: payload,
    });
  },

  async updateStatus(reportId: string, status: ReportStatus): Promise<Report> {
    return rawRequest<Report>(`/reports/${reportId}/status`, {
      method: "PATCH",
      body: {
        status,
      },
    });
  },
};

export const incidentsApi = {
  async list(limit = 50, offset = 0): Promise<Incident[]> {
    return rawRequest<Incident[]>(`/incidents${buildSearch({ limit, offset })}`);
  },
};
