export const f2 = (async (url: RequestInfo | URL) => {
  void url;
  return new Response('');
}) as unknown as typeof fetch;
export const f3 = (async (url: RequestInfo | URL, init?: RequestInit) => {
  void url; void init;
  return new Response('');
}) as typeof fetch;
declare function tx<T>(f: (t: number) => Promise<T>, cfg?: string): Promise<T>;
export const f4 = ((cb: never, cfg: never) => {
  void cb; void cfg;
  return Promise.resolve(1 as never);
}) as typeof tx;
export function mk(): typeof fetch {
  return (async (url: RequestInfo | URL) => {
    void url;
    return new Response('');
  }) as unknown as typeof fetch;
}
