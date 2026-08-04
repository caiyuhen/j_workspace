export type SessionStore = {
  getToken(): string | null;
  setToken(token: string): void;
  clearToken(): void;
};

export function createMemorySessionStore(
  initialToken: string | null = null,
): SessionStore {
  let token = initialToken;

  return {
    getToken() {
      return token;
    },
    setToken(nextToken: string) {
      token = nextToken;
    },
    clearToken() {
      token = null;
    },
  };
}

export function createBrowserSessionStore(
  key = "meda.session.token",
): SessionStore {
  return {
    getToken() {
      return window.localStorage.getItem(key);
    },
    setToken(token: string) {
      window.localStorage.setItem(key, token);
    },
    clearToken() {
      window.localStorage.removeItem(key);
    },
  };
}
