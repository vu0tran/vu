type R<T> = { done: false; value: T } | { done: true; value?: undefined };
declare function rd(): Promise<R<{ v: number }>>;
declare function rs(): R<{ v: number }>;
export async function f() {
  const { done, value } = await rd();
  if (done) return;
  const n: number = value.v;
}
export function h() {
  while (true) {
    const { done, value } = rs();
    if (done) break;
    const n: number = value.v;
  }
}
declare const reader: ReadableStreamDefaultReader<{ v: number }>;
export async function k() {
  const { done, value } = await reader.read();
  if (done) return;
  const n: number = value.v;
}
type K = { kind: 'a'; a: number } | { kind: 'b'; b: string };
export function m(r: { kind: 'a'; a: number; b?: undefined } | { kind: 'b'; b: string; a?: undefined }) {
  const { kind, a, b } = r;
  if (kind === 'a') { const x: number = a; } else { const y: string = b; const z: number = a; }
  switch (kind) { case 'a': { const x: number = a; break; } case 'b': { const y: string = b; break; } }
}
export function p(r: { ok: true; v: number } | { ok: false; e: string; v?: undefined }) {
  const { ok, v } = r;
  if (!ok) return;
  const q: number = v;
}
export function q(r: K) {
  const { kind } = r;
  switch (kind) { case 'a': { const x: number = r.a; break; } case 'b': { const y: string = r.b; break; } }
  if (kind === 'a') { const x: number = r.a; }
}
