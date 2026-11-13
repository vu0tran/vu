abstract class SA<T extends string> extends Array<T> {
  constructor(str: string) { super(); const p = str.split(',') as this; return p.filter((i) => typeof i === 'string' && i.length); }
}
class CS<T extends string> extends SA<T> { constructor(s: string) { super(s); } }
class AM extends CS<'a' | 'b'> {
  constructor(s: string) { super(s); for (const n of this) { const z: 'z' = n; } }
}
export const x: 'z' = new AM('a').length;
class E2 extends Error { k = 1; }
export const y: 'z' = new E2().message;
export class K { o: CS<'console' | 'file'> = ['console'] as unknown as CS<'console' | 'file'>; }
export const arr: { [n: number]: 'a' | 'b'; length: number } = ['a'];
export const w: CS<'a' | 'b'> = ['a'];
