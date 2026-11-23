declare const R: any;
declare const f: any; declare const B: any;
export function C0() {
  const el = <i />;
  return <B onClick={() => el} />;
}
export function C1() {
  const el = <i />;
  return <B onClick={() => { return el; }} />;
}
export function C2() {
  return <B onClick={() => { if (f) return x; var x = <i />; return null; }} />;
}
export function C3() {
  return <B onClick={() => { if (f) { const x = <i />; } return x; }} />;
}
export function C4() {
  return <B onClick={() => { const x = <i />; { const x = 1; return x; } }} />;
}
export function C5() {
  return <B onClick={() => { const g = () => { const x = <i />; return 1; }; return x; }} />;
}
export function C6() {
  return <B onClick={(x = <i />) => { return x; }} />;
}
export function C7() {
  return <B onClick={() => { for (const x of [<i />]) {} return x; }} />;
}
export function C8() {
  return <B onClick={() => { for (let x = <i />;;) { return x; } }} />;
}
export function C9() {
  return <B onClick={() => { const x = <></>; return x; }} />;
}
export function C10() {
  return <B onClick={() => { const x = <i /> as any; return x; }} />;
}
export function C11() {
  return <B onClick={() => { const x = f() || <i />; return x; }} />;
}
declare const x: any;
