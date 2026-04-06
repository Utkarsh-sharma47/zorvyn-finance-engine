import axios from 'axios';

import { API_BASE_URL } from '../config/apiBase';

/**
 * Axios instance: paths are relative to API_BASE_URL (e.g. /auth/me under /api/v1).
 */
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    Accept: 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function isAuthPublicRequest(url) {
  const u = String(url);
  return u.includes('/auth/login') || u.includes('/auth/register');
}

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const url = String(error.config?.url ?? '');
    if (status === 401 && !isAuthPublicRequest(url)) {
      localStorage.removeItem('token');
      if (typeof window !== 'undefined') {
        const path = window.location.pathname;
        if (!path.startsWith('/login') && !path.startsWith('/register')) {
          window.location.assign('/login');
        }
      }
    }
    return Promise.reject(error);
  },
);

export default api;
