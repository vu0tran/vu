declare const R: any;
declare const f: any; declare const B: any; declare const createElement: any; declare const x: any;
export function C0() {
  return <B onClick={() => { <i />; }} />;
}
export function C1() {
  return <B onClick={() => { let x; x = <i />; }} />;
}
export function C2() {
  return <B onClick={() => { const x = f(<i />); }} />;
}
export function C3() {
  return <B onClick={() => { const x = [<i />]; }} />;
}
export function C4() {
  return <B onClick={() => { const x = 1 ? <i /> : null; }} />;
}
export function C5() {
  return <B onClick={() => { const x = (<i />); }} />;
}
export function C6() {
  return <B onClick={() => { var x = <i />; }} />;
}
export function C7() {
  return <B onClick={() => (<i />) satisfies any} />;
}
export function C8() {
  return <B onClick={() => 1 + <i />} />;
}
export function C9() {
  return <B onClick={async () => await <i />} />;
}
export function C10() {
  return <B onClick={async () => { return await <i />; }} />;
}
export function C11() {
  return <B onClick={() => { if (<i />) {} }} />;
}
export function C12() {
  return <B onClick={() => { for (const a of [<i />]) {} }} />;
}
export function C13() {
  return <B onClick={() => { switch (<i />) {} }} />;
}
export function C14() {
  return <B onClick={() => { for (let a = <i />;;) {} }} />;
}
export function C15() {
  return <B onClick={() => { const x = { a: <i /> }; }} />;
}
export function C16() {
  return <B onClick={() => { const x = 1 && <i />; }} />;
}
export function C17() {
  return <B onClick={() => { const x = f() || <i />; }} />;
}
export function C18() {
  return <B onClick={() => { const x = (f(), <i />); }} />;
}
export function C19() {
  return <B onClick={() => { return (f(), <i />); }} />;
}
export function C20() {
  return <B onClick={() => { return <i />, 1; }} />;
}
export function C21() {
  return <B onClick={() => { if (1) {} else { return <i />; } }} />;
}
export function C22() {
  return <B onClick={() => { if (1) {} else return <i />; }} />;
}
export function C23() {
  return <B onClick={() => 1 ? f() : <i />} />;
}
export function C24() {
  return <B onClick={() => 1 ? createElement('i') : 0} />;
}
export function C25() {
  return <B onClick={() => { const x = createElement('i'); }} />;
}
export function C26() {
  return <B onClick={() => { const [a] = <i />; }} />;
}
export function C27() {
  return <B onClick={() => { x.y = <i />; }} />;
}
export function C28() {
  return <B onClick={() => { using x = <i />; }} />;
}
export function C29() {
  return <B onClick={() => { const x = <i /> as any; }} />;
}
export function C30() {
  return <B onClick={() => { return <i /> as any; }} />;
}
export function C31() {
  return <B onClick={() => { return (<i />); }} />;
}
export function C32() {
  return <B onClick={() => { return ((<i />)); }} />;
}
export function C33() {
  return <B onClick={() => { const x = 1, y = <i />; }} />;
}
export function C34() {
  return <B onClick={() => { export1: while (1) { break; } return <i />; }} />;
}
export function C35() {
  return <B onClick={() => { while (<i />) {} }} />;
}
export function C36() {
  return <B onClick={() => { do {} while (<i />); }} />;
}
export function C37() {
  return <B onClick={() => { for (const a in <i />) {} }} />;
}
export function C38() {
  return <B onClick={() => { for (;<i />;) {} }} />;
}
export function C39() {
  return <B onClick={() => { const x = 1 ?? <i />; }} />;
}
export function C40() {
  return <B onClick={() => { class K { m() { return <i />; } } }} />;
}
export function C41() {
  return <B onClick={() => { function g() { return <i />; } }} />;
}
