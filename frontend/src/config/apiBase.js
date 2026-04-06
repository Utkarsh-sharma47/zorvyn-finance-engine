/**
 * Absolute API root for all HTTP clients (Axios and fetch).
 * Must be set in the environment (see frontend/.env.example). No trailing slash.
 */
const raw = import.meta.env.VITE_API_BASE_URL;

if (typeof raw !== 'string' || !raw.trim()) {
  throw new Error(
    'VITE_API_BASE_URL is not set. Copy frontend/.env.example to .env.local and define the backend URL (e.g. the FastAPI /api/v1 prefix).',
  );
}

export const API_BASE_URL = raw.trim().replace(/\/+$/, '');
