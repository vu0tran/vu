type Shape = { [k: string]: { _def: number } };
function f<F extends Shape>(s: F) {
  for (const key in s) {
    const v = s[key];
    const d: string = v._def;
  }
}
function g<F extends Shape>(s: F, k: keyof F) { const d: string = s[k]._def; }
function h<F extends Shape>(s: F, k: Extract<keyof F, string>) { const d: string = s[k]._def; }
export {};
