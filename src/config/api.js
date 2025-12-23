// src/config/api.js
// Replace with your backend IP (no protocol/port)
export const API_HOST = '192.168.68.60';
export const API_PORT = 8000;
export const buildApiBase = (host = API_HOST, port = API_PORT) =>
  `http://${host}:${port}`;
export const API_BASE = buildApiBase();
