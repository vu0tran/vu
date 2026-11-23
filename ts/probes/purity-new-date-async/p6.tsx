import { useState } from 'react';
declare const f: any;
export async function Comp1() {
  return <i n={Math.random()} />;
}
export async function Comp2() {
  if (f) { useState(1); }
  return <i />;
}
export const Comp3 = async () => <i n={Date.now()} />;
export async function useHook() {
  return Math.random();
}
export async function Comp4() {
  let x = 1;
  const g = () => { x = 2; };
  g();
  return <i n={x} />;
}
export function Comp5() {
  return <i n={Math.random()} />;
}
export const Comp6 = async function () { return <i n={Date.now()} />; };
export async function* Comp7() { return <i n={Date.now()} />; }
export function* Comp8() { return <i n={Date.now()} />; }
