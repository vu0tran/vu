declare const d: { m: number } | null | undefined;
declare const r: { data?: { m: number } | null };
function f4() {
  if (!d) {
    if (!d) throw new Error();
    const y: string = d;
  }
  const x: string = d;
}
function f5() {
  if (!r.data) {
    if (!r.data) throw new Error();
    const y: string = r.data;
  }
  const x: string = r.data;
}
function f6() {
  if (!r.data) {
    throw new Error();
  }
  const x: string = r.data;
}
export {};
