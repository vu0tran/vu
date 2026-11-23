declare const R: any;
declare const f: any; declare const B: any; declare const memo: any;
export function Outer() {
  const Inner = () => <i />;
  f(<B x={Inner} />);
  return null;
}
export function Outer2() {
  const Inner = () => <i />;
  const el = <B x={Inner} />;
  return el;
}
export function Outer3() {
  const Inner = memo(() => f(<i />));
  return <B x={Inner} />;
}
export function Outer4() {
  const Inner = memo(() => <i />);
  return <B x={Inner} />;
}
export function Outer5() {
  function Inner() { f(<i />); return null; }
  return <B x={Inner} />;
}
