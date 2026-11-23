declare function f(): Promise<void>;
const run = async () => {
  const h = { a: 1 };
  try {
    await f();
    return { ...h, error: undefined };
  } catch (error) {
    return { ...h, error };
  }
};
export async function t1() {
  const { a, error } = await run();
  return [a, error.message];
}
declare const u: { e: undefined } | { e: any };
export function t2() {
  const { e } = u;
  return e.x;
}
export function t3() {
  const e = u.e;
  return e.x;
}
