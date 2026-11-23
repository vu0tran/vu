declare const R: any;
declare const f: any; declare const B: any; declare const createElement: any; declare const y: any;
const x0 = <i />;
export function C0() {
  return <B onClick={() => { const x = <i />; return x; }} />;
}
export function C1() {
  return <B onClick={() => { let x = <i />; return x; }} />;
}
export function C2() {
  return <B onClick={() => { var x = <i />; return x; }} />;
}
export function C3() {
  return <B onClick={() => { const x = f(); return x; }} />;
}
export function C4() {
  return <B onClick={() => { const x = 1 ? <i /> : null; return x; }} />;
}
export function C5() {
  return <B onClick={() => { const x = (<i />); return x; }} />;
}
export function C6() {
  return <B onClick={() => { const x = <i />; return 1 ? x : null; }} />;
}
export function C7() {
  return <B onClick={() => { const x = <i />; return (x); }} />;
}
export function C8() {
  return <B onClick={() => { let x; x = <i />; return x; }} />;
}
export function C9() {
  return <B onClick={() => { const x = f(<i />); return x; }} />;
}
export function C10() {
  return <B onClick={() => { const x = <i />; const y = x; return y; }} />;
}
export function C11() {
  return <B onClick={() => { const x = createElement('i'); return x; }} />;
}
export function C12() {
  return <B onClick={() => { return y; }} />;
}
export function C13() {
  return <B onClick={() => { const x = <i />; return x || null; }} />;
}
export function C14() {
  return <B onClick={() => { const x = <i />; { return x; } }} />;
}
export function C15() {
  return <B onClick={() => { if (1) { const x = <i />; return x; } }} />;
}
export function C16() {
  return <B onClick={() => { const x = <i />; return () => x; }} />;
}
export function C17() {
  return <B onClick={() => x0} />;
}
export function C18() {
  return <B onClick={() => { const x = <i />; return x.y; }} />;
}
export function C19() {
  return <B onClick={() => { const { x } = { x: <i /> }; return x; }} />;
}
export function C20() {
  return <B onClick={() => 1 ? (2 ? null : <i />) : 0} />;
}
export function C21() {
  return <B onClick={() => (1 ? null : (<i />))} />;
}
export function C22() {
  return <B onClick={() => f() && (<i />)} />;
}
export function C23() {
  return <B onClick={() => (f(), (<i />))} />;
}
export function C24() {
  return <B onClick={() => { return; }} />;
}
export function C25() {
  return <B onClick={() => { const x = <i />; function g() { return x; } return 1; }} />;
}
