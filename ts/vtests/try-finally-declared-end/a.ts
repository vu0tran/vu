// a variable assigned in a loop inside a try block, back at its declared type when the try block
// ends, read in the finally block and after it (a package's chat stream)
declare function next(): Promise<number>;
declare const sig: { aborted: boolean };
export function g() {
  let pending: Promise<number> | undefined;
  try {
    while (!sig.aborted) {
      pending ??= next();
      if (sig.aborted) continue;
      pending = undefined;
    }
  } finally {
    void pending?.catch(() => {});
  }
  return [pending];
}
export function h() {
  let p: string | number = 1;
  try {
    for (let i = 0; i < 3; i++) p = i > 1 ? 'a' : 2;
  } finally {
    p;
  }
  return [p];
}
export const x: number = g();
export const y: number = h();
