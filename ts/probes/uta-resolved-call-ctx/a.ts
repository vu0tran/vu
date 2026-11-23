declare function hoisted<T>(factory: () => T): T;
export const { s } = hoisted(() => ({
  s: {
    scenario: 'success' as 'success' | 'other',
    last: undefined as unknown,
    n: null as unknown,
  },
}));
declare function id<T>(x: T): T;
export const k = id({ v: undefined as unknown });
declare function onlyObj(x: { v: unknown }): void;
onlyObj({ v: undefined as unknown });
