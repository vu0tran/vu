declare const R: any;
declare const f: any; declare const B: any;
export function C0() {
  return <B onClick={() => <i /> || f()} />;
}
export function C1() {
  return <B onClick={() => (<i /> ? 1 : 2)} />;
}
export function C2() {
  return <B onClick={() => { let x = <i />; x = 1; return x; }} />;
}
export function C3() {
  return <B onClick={() => { const x = R.createElement('i'); return x; }} />;
}
export function C4() {
  return <B onClick={() => { return () => <i />; }} />;
}
export function C5() {
  return <B onClick={(x: any) => { return x; }} />;
}
export function C6() {
  return <B onClick={() => { function x() {} return x; }} />;
}
export function C7() {
  return <B onClick={() => { switch (f) { default: { const x = <i />; return x; } } }} />;
}
export function C8() {
  return <B onClick={() => { try { const x = <i />; return x; } catch { return null; } }} />;
}
export function C9() {
  return <B onClick={() => { const [x] = [<i />]; return x; }} />;
}
export function C10() {
  return <B onClick={() => document.createElement('i')} />;
}
