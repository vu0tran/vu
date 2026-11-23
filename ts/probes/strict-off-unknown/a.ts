// strict: false: unknown's apparent type is {}, a truthy unknown stays unknown
declare function isRecord(v: unknown): v is Record<string, unknown>;
export function msg(error: unknown): string {
  if (!isRecord(error)) return String(error);
  return `${error}`;
}
export function rethrow(failure: unknown) {
  if (failure) throw failure;
}
export function data(d: unknown) {
  return d as { errors?: unknown } | string | undefined;
}
declare const k: string | null;
export const b = !!(k && k.length > 0);
declare function loadJson<T>(p: string, d: T): T;
declare function restore(s: { a: number }): number;
restore(loadJson("x", null));
