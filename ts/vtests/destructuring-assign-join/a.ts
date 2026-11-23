// A destructuring assignment in one branch assigns its targets: after the if, their types are
// joined with the other branch's (it was the other branch's alone, null, then never below).
type H = { email: string } | null;
declare function trigger(): { data: H; n: number; list: string[] };
declare const flag: boolean;
export function a1(): number {
  let human: H = null;
  if (flag) ({ data: human } = trigger());
  const e: number = human?.email;
  return e;
}
export function a2(): number {
  let human: H = null;
  let n: number | undefined;
  let first: string[] | undefined;
  if (flag) ({ data: human, n, list: first } = trigger());
  const x: string = n;
  const y: number = first;
  return human ? 1 : 0 + x.length + y;
}
export function a3(): number {
  let human: H = null;
  for (const i of [1, 2]) {
    if (i) ({ data: human } = trigger());
  }
  const e: number = human?.email;
  return e;
}
