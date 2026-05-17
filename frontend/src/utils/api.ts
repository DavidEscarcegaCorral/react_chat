const API_BASE = 'http://localhost:8000';

function getToken(): string | null {
  return sessionStorage.getItem('token');
}

function getUsername(): string | null {
  return sessionStorage.getItem('username');
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: Bearer  } : {}),
    ...options.headers,
  };
  
  const response = await fetch(${API_BASE}, {
    ...options,
    headers,
  });
  
  if (response.status === 401) {
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('username');
    window.location.href = '/';
    throw new Error('Sesión expirada');
  }
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error de servidor' }));
    throw new Error(error.detail || 'Error en la solicitud');
  }
  
  return response.json();
}

export const authApi = {
  register: (username: string, password: string) =>
    apiRequest<{ status: string; message: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  
  login: (username: string, password: string) =>
    apiRequest<{
      status: string;
      message: string;
      token: string;
      username: string;
      public_key: string;
    }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  
  logout: () =>
    apiRequest<{ status: string; message: string }>('/auth/logout', {
      method: 'POST',
    }),
  
  verify: () =>
    apiRequest<{ status: string; username: string }>('/auth/verify', {
      method: 'GET',
    }),
};

export const serverApi = {
  run: (protocol: string) =>
    apiRequest<{ status: string; error?: string }>('/server/run', {
      method: 'POST',
      body: JSON.stringify({ protocol }),
    }),
  
  shutdown: () =>
    apiRequest<{ status: string }>('/server/shutdown', {
      method: 'POST',
    }),
  
  status: () =>
    apiRequest<{
      running: boolean;
      protocol: string | null;
      host: string;
      port: number;
      clients: string[];
      history_len: number;
    }>('/server/status', {
      method: 'GET',
    }),
  
  clear: () =>
    apiRequest<{ status: string }>('/server/clear', {
      method: 'DELETE',
    }),
};

export const clientApi = {
  login: (username: string) =>
    apiRequest<{ status: string; error?: string }>('/client/login', {
      method: 'POST',
      body: JSON.stringify({ username }),
    }),
  
  logout: (username: string) =>
    apiRequest<{ status: string }>('/client/logout', {
      method: 'POST',
      body: JSON.stringify({ username }),
    }),
  
  send: (message: string, username: string, recipient: string = 'all') =>
    apiRequest<{ status: string; error?: string; recipient: string }>('/client/send', {
      method: 'POST',
      body: JSON.stringify({ message, username, recipient }),
    }),
  
  history: () =>
    apiRequest<{ history: string[] }>('/client/history', {
      method: 'GET',
    }),
  
  clients: () =>
    apiRequest<{ clients: string[] }>('/client/clients', {
      method: 'GET',
    }),
  
  dms: (username: string) =>
    apiRequest<{ dms: string[] }>(/client/dms/, {
      method: 'GET',
    }),
};

export { getUsername };
