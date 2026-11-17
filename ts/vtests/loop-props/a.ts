// a property assigned in a loop, not narrowed before it: its declared type at the head
interface K { $page?: number; s: string | number }
declare function more(): boolean;
export function f(m: Record<string, string>, keys: string[]) {
  const k: K = { $page: 0, s: 1 };
  let n = 0;
  do {
    const v: boolean = k.$page;
    k.$page = (k.$page ?? 0) + 1;
    const w: boolean = k.$page;
    if (more()) break;
    k.s = 'x';
    const y: boolean = k.s;
    n++;
  } while (n < 3);
  const k2: K = { s: 1 };
  while (more()) {
    const z: boolean = k2.s;
    k2.s = 2;
  }
  for (const key of keys) {
    const r = { body: m[key] as string | undefined };
    if (r.body) { const b: number = r.body; }
    r.body = undefined;
  }
}
