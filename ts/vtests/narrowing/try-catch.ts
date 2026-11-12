// A catch block starts with the types before the try block and right after each assignment in it
export {};
declare function f(): string;
declare function g(): number;
function t1() {
  let x: string | number | undefined = undefined;
  try { x = f(); x = g(); } catch { const a: boolean = x; }
  const b: boolean = x;
}
function t2() {
  let x: string | undefined;
  try { x = f(); } catch (e) { x = 'fallback'; }
  const b: boolean = x;
}
function t3() {
  let x: string | boolean = 'a';
  try { if (Math.random()) x = true; } catch { const a: number = x; }
  const b: number = x;
}
function t4() {
  let x = 'a' as string | null;
  try { x = null; } catch { return; }
  const b: number = x;
}

function u6() {
  let x: string | number | boolean = 1;
  try {
    try { x = 's'; } catch { x = true; }
  } catch { const a: null = x; }
  const b: null = x;
}
function u8() {
  let x: string | undefined;
  try { x = f(); } catch { const a: null = x; throw 1; }
  const b: null = x;
}
