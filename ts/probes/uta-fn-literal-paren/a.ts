declare function jsonResponse(x: unknown): Response;
export const fetchFn = (async (url: RequestInfo | URL, init?: RequestInit) => {
  void url; void init;
  return jsonResponse({});
}) as typeof fetch;
declare function one(a: string): number;
declare function one(a: number): number;
export const g = ((a: string | number) => 1) as typeof one;
