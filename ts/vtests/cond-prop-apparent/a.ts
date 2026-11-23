export {};
// a property of a conditional type read through its apparent type (the base constraint), an object
// or an intersection: Awaited<E> of an E constrained to an object
export async function f<E extends { id: string }>(ids: string[], load: (id: string) => Promise<E>) {
  const results = await Promise.allSettled(ids.map((id) => load(id)));
  const es = results.flatMap((r) => r.status === 'fulfilled' ? [r.value] : []);
  const x: number = es;
  const y: number = es.map((e) => e.id);
}
type Ref<T> = { value: T };
type Shallow<T> = Ref<T> & { s: true };
export function g<T>(s: Ref<number> extends T ? Shallow<T> : Shallow<T>) { const n: number = s.value; }
export function h<T>(s: T extends string ? { a: 1; b: T } : { a: 2; b: T }) { const n: string = s.a; }
