import type { TokenPair } from "../types/api";


const ACCESS_TOKEN_KEY = "trust-system.access-token";
const REFRESH_TOKEN_KEY = "trust-system.refresh-token";

let memoryAccessToken: string | null = null;
let memoryRefreshToken: string | null = null;

function canUseStorage(): boolean {
  return typeof window !== "undefined" && typeof window.sessionStorage !== "undefined";
}

function notifySessionChange(eventName = "trust-system:session-changed"): void {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(eventName));
  }
}

function readToken(key: string): string | null {
  if (!canUseStorage()) {
    return null;
  }

  return window.sessionStorage.getItem(key);
}

export function getAccessToken(): string | null {
  return memoryAccessToken ?? readToken(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return memoryRefreshToken ?? readToken(REFRESH_TOKEN_KEY);
}

export function hasSessionTokens(): boolean {
  return Boolean(getAccessToken() || getRefreshToken());
}

export function setSessionTokens(tokens: TokenPair): void {
  memoryAccessToken = tokens.access_token;
  memoryRefreshToken = tokens.refresh_token;

  if (canUseStorage()) {
    window.sessionStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    window.sessionStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  }

  notifySessionChange();
}

export function clearSessionTokens(): void {
  memoryAccessToken = null;
  memoryRefreshToken = null;

  if (canUseStorage()) {
    window.sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    window.sessionStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  notifySessionChange();
}

export function signalAuthExpiry(): void {
  clearSessionTokens();
  notifySessionChange("trust-system:auth-expired");
}
