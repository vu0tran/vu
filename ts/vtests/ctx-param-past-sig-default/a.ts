type S = <T = unknown>(m: string, p?: Record<string, unknown>) => Promise<T>;
export const x: { send: S } = {
  send<T = unknown>(m: string, p: Record<string, unknown> = {}, t = 30) {
    const q: string = t;
    return Promise.resolve(null as T);
  },
};
export const y: { send: S } = {
  send(m, p = {}, t = 30) {
    const q: string = t;
    return Promise.resolve(null as any);
  },
};
