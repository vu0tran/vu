declare function work(): void;
declare function n(): number;
function f1(): number {
  let success = false;
  try { work(); success = true; return 1; }
  finally { if (!success) work(); const z: true = success; }
}
function f2() {
  let x: string | number | undefined = undefined;
  try { x = "a"; work(); x = 1; }
  finally { const z: number = x; }
  const after: string = x;
}
function f3(y: string | undefined) {
  try { if (!y) return; work(); }
  finally { work(); }
  const s: string = y;
}
function f4() {
  let x: string | number = "s";
  try { work(); }
  finally { x = 1; }
  const s: string = x;
}
function f5() {
  let x = 0;
  try { x = n(); } finally { work(); }
  const s: string = x;
}
function f6(): number {
  try { return 1; } finally { work(); }
}
export {};
