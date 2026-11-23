interface Ctx { a: { f: (x: number) => number; g: string }; b: number }
declare function mk(p: Partial<Ctx>): void;
declare function mk2(p: Ctx): void;
declare const anyf: any;
declare const s: string;
mk({ a: { f: anyf, g: 'x' } } as any);
mk({ b: 1 } as any);
mk2({ b: 1 } as any);
mk({ zz: 1 } as any);
mk(s as any);
mk({ a: anyf } as any);
mk({ b: 1 } as Ctx);
