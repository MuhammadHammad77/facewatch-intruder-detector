const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

const RAILWAY_URL = 'https://facewatch-intruder-detector-production.up.railway.app';

export const API_URL = isLocal ? 'http://localhost:8000' : RAILWAY_URL;

export const BACKEND_URL = isLocal ? 'http://localhost:8000' : RAILWAY_URL;

export const getWsUrl = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = isLocal ? 'localhost:8000' : 'facewatch-intruder-detector-production.up.railway.app';
  return `${protocol}//${host}/api/alerts/ws`;
};
