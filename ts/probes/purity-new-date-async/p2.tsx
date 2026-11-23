declare const f: any;
export async function Page1() {
  const v = await f();
  return <i v={v} n={new Date()} />;
}
export function Page2() {
  const n = new Date();
  return <i n={n} />;
}
export async function Page3() {
  const n = new Date();
  return <i n={n} />;
}
export default async function Page4() {
  return <i n={new Date()} />;
}
export function Comp5() {
  function get() {
    return new Date();
  }
  return <i n={get()} />;
}
export function Comp6() {
  const x = f() ? f(new Date()) : null;
  return <i n={x} />;
}
export function Comp7() {
  const x = { createdAt: new Date().toISOString() };
  return <i n={x} />;
}
