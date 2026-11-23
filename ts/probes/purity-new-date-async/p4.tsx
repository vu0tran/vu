declare const f: any;
export function Comp1() {
  function get() {
    return Date.now();
  }
  return <i />;
}
export function Comp2() {
  const get = () => {
    f(new Date());
  };
  get();
  return <i />;
}
export function Comp3() {
  const get = () => new Date().getTime();
  return <i n={get()} />;
}
export function Comp4() {
  const d = new Date();
  return <i n={d} />;
}
export function Comp5() {
  const x = f(new Date());
  return <i n={x} />;
}
export function Comp6() {
  return <i n={Date.now()} />;
}
export function Comp7() {
  const x = f ? new Date() : null;
  return <i n={x} />;
}
export function Comp8() {
  let x = null;
  if (f) x = new Date();
  return <i n={x} />;
}
export function Comp9() {
  if (f) return null;
  const n = new Date();
  return <i n={n} />;
}
export function Comp10() {
  if (f) {
    return null;
  }
  return <i n={new Date()} />;
}
