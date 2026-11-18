interface A { load(): number; a: 1 }
interface B { save(x: string): void; b: 2 }
interface C2 { other: string }
declare function isA(x: unknown): x is A;
export function wrap<T extends A | B | C2>(orig: T): T {
  return new Proxy(orig, {
    get: (target, prop) => {
      if (isA(orig)) {
        if (prop === 'load' && 'load' in target) {
          return async (v: number) => {
            const f = (target[prop] as () => number).bind(target);
            const h: string = target;
            return f() + v;
          };
        }
      }
      return (target as any)[prop];
    },
  });
}
