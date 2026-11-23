declare function takes(x: string): number;
export function f(onChange: () => void): number {
  let raf = 0;
  const sync = () => {
    raf = 0;
    onChange();
    if (raf > 2) {
      return;
    }
    if (raf < 1) {
      raf = takes(sync);
    }
  };
  const sync3 = () => {
    onChange();
    if (raf > 2) {
      return;
    }
    raf = takes(sync3);
  };
  return raf;
}
declare function fail(): never;
declare const ok: boolean;
export function g(): number {
  let raf = 0;
  const sync5 = () => {
    if (ok) fail();
    raf = takes(sync5);
  };
  const log = (m: string) => { console.log(m); };
  const sync6 = () => {
    log('x');
    raf = takes(sync6);
  };
  return raf;
}
