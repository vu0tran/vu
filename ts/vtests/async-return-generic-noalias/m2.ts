export function mk<T>(req: () => Promise<T>) {
  const cache = {
    get(k: string): T | undefined { return undefined; },
    async load(k: string): Promise<T> {
      const c = cache.get(k);
      if (c !== undefined) return c;
      return await req();
    },
  };
  return cache;
}
export function mk3<T>(req: () => T) {
  const cache = {
    get(k: string): T | undefined { return undefined; },
    load(k: string): T {
      const c = cache.get(k);
      if (c !== undefined) return c;
      return req();
    },
  };
  return cache;
}
