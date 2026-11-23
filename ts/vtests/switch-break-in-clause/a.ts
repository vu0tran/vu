// A break inside a switch clause (not its last statement): what's known there joins after it.
type K = 'a' | 'b' | 'c' | 'd';
declare const k: K;
declare const flag: boolean;
export function f1() {
  let x: string | number | boolean = true;
  switch (k) {
    case 'a':
      x = 1;
      if (flag) break;
      x = 'one';
      break;
    case 'b':
      x = 2;
      break;
    default:
      return;
  }
  const n: boolean = x;
}
export function f2() {
  let x: string | number | undefined;
  switch (k) {
    case 'a':
      if (flag) { x = 1; break; } else { x = 's'; }
      break;
    case 'b': {
      x = 2;
      if (flag) break;
      x = undefined;
      break;
    }
  }
  const n: boolean = x;
}
export function f3(xs: number[]) {
  let x: string | number | null = null;
  switch (k) {
    case 'a':
      for (const v of xs) {
        if (v) break;
      }
      x = 'loop';
      break;
    case 'b':
      try {
        x = 3;
        if (flag) break;
      } finally {
        x = 4;
      }
      break;
  }
  const n: boolean = x;
}
export function f4() {
  let acted: 'a' | 'b' | undefined;
  switch (k) {
    case 'a':
      if (flag) break;
      acted = k;
      break;
    case 'b':
      if (flag) break;
      acted = k;
      break;
    case 'c':
      return;
  }
  const n: boolean = acted;
  const m: boolean = k;
}
