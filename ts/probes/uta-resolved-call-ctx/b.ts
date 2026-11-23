declare function hoisted<T>(factory: () => T): T;
export const a1 = hoisted(() => ({ v: undefined as unknown }));
export const a2 = hoisted(() => ({ s: { v: undefined as unknown, w: 'x' as 'x' | 'y' } }));
export const a3 = hoisted(() => ({ s: { t: { v: undefined as unknown } } }));
export const a4 = hoisted(() => ({ s: { v: undefined as string | undefined } }));
declare function h2(f: () => { s: { last: unknown } }): void;
h2(() => ({ s: { last: undefined as unknown } }));
declare function h3<T>(x: T): T;
export const a5 = h3({ s: { v: undefined as unknown } });
export const a6 = hoisted(() => {
  return { s: { v: undefined as unknown } };
});
export const a7 = hoisted(() => [{ v: undefined as unknown }]);
