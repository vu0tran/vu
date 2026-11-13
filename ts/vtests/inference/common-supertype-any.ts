interface EachRet<T extends any[] | [any]> { (name: string, fn: (...args: T) => void): void }
interface TE {
  <T extends any[] | [any]>(cases: ReadonlyArray<T>): EachRet<T>;
  <T>(cases: ReadonlyArray<T>): EachRet<T[]>;
}
declare const each: TE;
declare const tests: any[][] | string[][] | {}[][] | (string | number)[][];
each(tests)('x', (expression, expected) => { const z: 'z' = expression; });
declare const t2: string[][] | (string | number)[][];
each(t2)('x', (e) => { const z: 'z' = e; });
