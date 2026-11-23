// functions without a return value inside a function declaration whose return type is being inferred:
// their bodies checked once it has it (a package's createReadModel, used through ReturnType<typeof ...>)
function createOwner(key: string) {
  const getSnapshot = () => key;
  return {
    getSnapshot,
    subscribe: (l: () => void) => {
      void l;
      return () => {
        queueMicrotask(() => {
          const owners = registry.get(key);
          const n: number = owners!;
          void n;
        });
      };
    },
  };
}
const registry = new Map<string, ReturnType<typeof createOwner>>();
export const o: number = registry.get('a')!.getSnapshot;
declare function use(n: number): void;
export function f(x: string | undefined, y: { a?: { b: number } }) {
  if (!x) return undefined;
  const z = y.a;
  if (!z) return null;
  let w: string | number = 'a';
  w = 1;
  return { g: () => { use(x.length); use(z.b); const q: number = w; void q; }, h: [() => { use(x.length); }] };
}
