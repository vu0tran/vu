declare function isRecord(value: unknown): value is Record<string, unknown>;
declare const result: { data?: Record<string, any> | null; errors?: string[] };
declare const k: string;
export function f() {
  if (!result.errors?.length || !isRecord(result.data)) return;
  const parent = result.data[k];
  const n: [typeof parent] = 0;
}
declare const d2: Record<string, any> | null;
export function g() {
  if (!isRecord(d2)) return;
  const p = d2[k];
  const n: [typeof p] = 0;
}
