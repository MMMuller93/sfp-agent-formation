/**
 * Application configuration derived from environment variables.
 *
 * In development, Vite's proxy handles /v1 requests so the base URL
 * defaults to the current origin. In production, set VITE_API_URL to
 * the backend's public URL.
 */

interface AppConfig {
  /** Base URL for all API requests (no trailing slash). */
  apiBaseUrl: string;
  /** If true, the app is running in production mode. */
  isProduction: boolean;
}

export const config: AppConfig = {
  apiBaseUrl: import.meta.env.VITE_API_URL ?? "",
  isProduction: import.meta.env.PROD,
};
