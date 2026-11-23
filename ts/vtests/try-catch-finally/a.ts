declare function work(): Promise<void>;
const retry = { current: false };
const flag = { current: true };
export async function f() {
  try {
    await work();
    retry.current = false;
  } catch {
    const b: true = retry.current;
    if (!retry.current) retry.current = true;
  } finally {
    flag.current = false;
  }
  const c: true = retry.current;
  const d: true = flag.current;
}
export function g(x: string | number) {
  let y = x;
  try {
    y = 1;
  } catch {
    const e: string | number = y;
  } finally {
    void 0;
  }
  const h: string | number = y;
  const i: boolean = h;
}
const again = { current: false };
export async function h() {
  try {
    await work();
  } catch {
    again.current = true;
  } finally {
    const k: true = again.current;
    if (again.current) again.current = false;
  }
  const l: true = again.current;
}
export async function r(): Promise<number> {
  try {
    again.current = true;
    return 1;
  } catch {
    return 2;
  } finally {
    again.current = false;
  }
}
