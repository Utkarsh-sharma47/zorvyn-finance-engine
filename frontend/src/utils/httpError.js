/**
 * Normalize Axios/FastAPI errors into a single user-facing string.
 * Handles: our ResponseModel envelope (`error`), Starlette `detail` string,
 * FastAPI validation arrays, and network/offline cases.
 */
export function parseAxiosError(err) {
  if (!err || typeof err !== 'object') {
    return 'Something went wrong';
  }

  if (!err.response) {
    if (err.code === 'ECONNABORTED') {
      return 'Request timed out. Try again.';
    }
    if (err.message === 'Network Error' || err.message?.includes('Network')) {
      return 'Cannot reach the server. Start the API (port 8000) and ensure the Vite proxy is enabled.';
    }
    return err.message || 'Network error';
  }

  const status = err.response.status;
  const data = err.response.data;

  if (data && typeof data === 'object') {
    if (typeof data.error === 'string' && data.error.length > 0) {
      return data.error;
    }
    const d = data.detail;
    if (typeof d === 'string' && d.length > 0) {
      return d;
    }
    if (Array.isArray(d)) {
      return d
        .map((e) => {
          if (typeof e === 'string') return e;
          if (e && typeof e.msg === 'string') return e.msg;
          return JSON.stringify(e);
        })
        .join('; ');
    }
  }

  if (status === 404) {
    return 'API route not found — check that the URL is /api/v1/auth/login and the backend is running.';
  }

  return `Request failed (${status})`;
}
