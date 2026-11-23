declare const R: any;
declare const f: (x: unknown) => void;
declare const B: any;
export function C1() {
  return <B onClick={() => f({ c: <i /> })} />;
}
export function C2() {
  return <B onClick={() => f(<i />)} />;
}
export function C3() {
  return <B onClick={() => { f({ c: <i /> }); }} />;
}
export function C4() {
  return <B onClick={() => ({ c: <i /> })} />;
}
export function C5() {
  return <B onClick={() => [<i key="a" />]} />;
}
export function C6() {
  return <B onClick={() => { const x = <i />; f(x); }} />;
}
export function C7() {
  return <B onClick={() => { if (1) { f(<i />); } }} />;
}
export function C8() {
  return <B onClick={() => { switch (1) { case 1: f(<i />); } }} />;
}
export function C9() {
  return <B onClick={() => { try { f(<i />); } catch {} }} />;
}
export function C10() {
  return <B onClick={() => { return <i />; }} />;
}
export function C11() {
  return <B onClick={() => <i />} />;
}
export function C12() {
  return <B onClick={() => f(1) || <i />} />;
}
export function C13() {
  return <B onClick={function () { f(<i />); }} />;
}
export function C14() {
  return <B onClick={() => (1 ? <i /> : null)} />;
}
export function C15() {
  return <B onClick={async () => { await f(<i />); }} />;
}
export function C16() {
  return <B onClick={() => { f(1); f({ d: <i /> }); }} />;
}
export function C17() {
  const g = { onSubmit: () => { f({ d: <i /> }); } };
  return <B g={g} />;
}
