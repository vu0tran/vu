// The first inference pass checks a context-sensitive object literal's other properties.
declare function mk<O extends readonly unknown[]>(a: Readonly<{ d?: Readonly<O>; c: (o: Readonly<O>) => void }>): O;
export const x = mk({ d: [{ g: [] as string[] }], c([{ g }]) { g.length; } });
declare function mk5<O>(a: { d?: O; c: (o: O) => void }): O;
export const z3 = mk5({ d: [{ g: [] as string[] }], c([o]) { o.g.length; } });
export const z5: string = mk5({ d: 1, c: (o) => { o.toFixed(); } });
