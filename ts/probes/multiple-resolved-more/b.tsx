import * as React from "react";
declare function dec(): void;
enum E { A = 1 }
namespace N {
  export const p = new Promise<void>((resolve) => { resolve(); resolve(); });
}
class S {
  @dec2(() => 1) m(): Promise<void> {
    return new Promise<void>((resolve, reject): void => {
      const el = <div onClick={() => { resolve(); resolve(); }} />;
      resolve(); (reject as any)(); reject!(); resolve();
    });
  }
  overload(): void;
  overload(x?: number): void {}
}
const q = new Promise((resolve: (v: number) => void) => { resolve(1); resolve(2); }) as Promise<number>;
function g<T>(): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    if (x satisfies boolean) resolve(1 as T); else reject();
    resolve(2 as T);
  });
}
