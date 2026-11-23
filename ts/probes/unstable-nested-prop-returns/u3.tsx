declare const R: any;
declare const f: any; declare const B: any; declare const createElement: any;
export function C0() {
  return <B onClick={() => { return f(<i />); }} />;
}
export function C1() {
  return <B onClick={() => { return { c: <i /> }; }} />;
}
export function C2() {
  return <B onClick={() => { return [<i key='a' />]; }} />;
}
export function C3() {
  return <B onClick={() => { if (1) { return <i />; } }} />;
}
export function C4() {
  return <B onClick={() => { if (1) return <i />; return null; }} />;
}
export function C5() {
  return <B onClick={() => { switch (1) { case 1: return <i />; } }} />;
}
export function C6() {
  return <B onClick={() => { try { return <i />; } catch {} }} />;
}
export function C7() {
  return <B onClick={() => { for (;;) { return <i />; } }} />;
}
export function C8() {
  return <B onClick={() => { const x = <i />; return x; }} />;
}
export function C9() {
  return <B onClick={() => (<i />)} />;
}
export function C10() {
  return <B onClick={() => <></>} />;
}
export function C11() {
  return <B onClick={() => (1, <i />)} />;
}
export function C12() {
  return <B onClick={() => (f() as any) || <i />} />;
}
export function C13() {
  return <B onClick={() => (<i />) as any} />;
}
export function C14() {
  return <B onClick={() => { label: { return <i />; } }} />;
}
export function C15() {
  return <B onClick={() => { { return <i />; } }} />;
}
export function C16() {
  return <B onClick={() => { while (1) return <i />; }} />;
}
export function C17() {
  return <B onClick={() => { const g = () => <i />; return 1; }} />;
}
export function C18() {
  return <B onClick={() => f(1) ?? <i />} />;
}
export function C19() {
  return <B onClick={() => (1 ? f(<i />) : null)} />;
}
export function C20() {
  return <B onClick={() => (1 ? null : <i />)} />;
}
export function C21() {
  return <B onClick={() => { return 1 && (2 ? <i /> : null); }} />;
}
export function C22() {
  return <B onClick={() => R.createElement('i')} />;
}
export function C23() {
  return <B onClick={() => createElement('i')} />;
}
export function C24() {
  return <B onClick={() => { return createElement('i'); }} />;
}
export function C25() {
  return <B onClick={() => f(createElement('i'))} />;
}
export function C26() {
  return <B onClick={() => { try {} finally { return <i />; } }} />;
}
export function C27() {
  return <B onClick={() => { try {} catch { return <i />; } }} />;
}
export function C28() {
  return <B onClick={() => { do { return <i />; } while (0); }} />;
}
export function C29() {
  return <B onClick={() => { for (const a of []) return <i />; }} />;
}
export function C30() {
  return <B onClick={() => `${<i />}`} />;
}
export function C31() {
  return <B onClick={() => void <i />} />;
}
export function C32() {
  return <B onClick={() => { throw <i />; }} />;
}
export function C33() {
  return <B onClick={() => { f(<i />); return null; }} />;
}
export function C34() {
  return <B onClick={function () { return <i />; }} />;
}
export function C35() {
  return <B onClick={function () { return f(<i />); }} />;
}
export function C36() {
  return <B onClick={function () { return 1 ? <i /> : null; }} />;
}
export function C37() {
  return <B onClick={function () { if (1) return <i />; }} />;
}
