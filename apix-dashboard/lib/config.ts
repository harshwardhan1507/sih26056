/**
 * APIx Dashboard Application Configuration
 *
 * Environment variables:
 * - NEXT_PUBLIC_API_BASE_URL: Target FastAPI server URL.
 *   If unset, live provider queries are directed to empty base or explicit fallback.
 */

export const config = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || "",
  isLiveApiConfigured(): boolean {
    return Boolean(this.apiBaseUrl && this.apiBaseUrl.trim().length > 0);
  },
  getEffectiveApiBaseUrl(): string {
    return this.apiBaseUrl.replace(/\/+$/, "");
  },
};
