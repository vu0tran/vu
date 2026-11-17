export function f1() {
  let ts: Date | null = null;
  const b = ts!.getTime();
}
export function f2() {
  let ts: Date | null = null;
  const h = () => { ts = new Date(); };
  const b = ts!.getTime();
}
export function f3() {
  let ts: Date | null = null;
  const b = ts!;
  const c: string = b;
}
export function f4(t: null) {
  const b = t!.getTime();
}
