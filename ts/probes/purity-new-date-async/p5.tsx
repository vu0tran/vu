import { useMemo, useState, useCallback, useEffect } from 'react';
declare const f: any;
export function Comp1() {
  const d = useMemo(() => new Date(), []);
  return <i n={d} />;
}
export function Comp2() {
  const [d] = useState(() => new Date());
  return <i n={d} />;
}
export function Comp3() {
  const cb = useCallback(() => new Date(), []);
  return <i n={cb} />;
}
export function Comp4() {
  useEffect(() => { f(new Date()); }, []);
  return <i />;
}
export function Comp5() {
  const d = useMemo(() => Date.now(), []);
  return <i n={d} />;
}
export function Comp6() {
  const d = (() => new Date())();
  return <i n={d} />;
}
export function Comp7() {
  const d = [1].map(() => new Date());
  return <i n={d} />;
}
export function Comp8() {
  const d = [1].map(() => Date.now());
  return <i n={d} />;
}
export function Comp9() {
  return <i onClick={() => f(new Date())} />;
}
export function Comp10() {
  const d = useMemo(() => { if (f) return null; return new Date(); }, []);
  return <i n={d} />;
}
