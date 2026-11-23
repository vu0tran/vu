interface Ctx { flag?: boolean; n?: number; s: string | undefined; o?: { x?: 'a' | 'b' } }
declare function work(): Promise<void>;
export async function f(m: Ctx) {
  m.flag = true;
  try {
    await work();
    m.flag = false;
  } catch {
    const a: string = m.flag;
  }
  const b: string = m.flag;
}
export async function g(m: Ctx) {
  m.n = 1;
  try {
    await work();
    m.n = 2;
    await work();
  } catch {
    const a: string = m.n;
  }
  const b: string = m.n;
}
export async function h(m: Ctx) {
  try {
    m.flag = undefined;
    await work();
  } catch {
    const a: string = m.flag;
  }
}
export function k(m: Ctx) {
  for (let i = 0; i < 3; i++) {
    if (i) m.flag = true;
  }
  const a: string = m.flag;
  if (m.o) {
    m.o.x = 'a';
    try { work(); m.o.x = 'b'; } catch { const q: number = m.o.x; }
  }
}
