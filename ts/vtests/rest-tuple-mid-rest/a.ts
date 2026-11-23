type Cb<T> = (err: Error | null, v?: T) => void;
interface R {
  del(...args: [...keys: string[], callback: Cb<number>]): Promise<number>;
  del(...args: [keys: string[], callback: Cb<number>]): Promise<number>;
  del(...args: string[]): Promise<number>;
  del(...args: [keys: string[]]): Promise<number>;
  mget(...args: [...keys: string[], callback: Cb<string[]>]): Promise<string[]>;
  mget(...args: string[]): Promise<(string | null)[]>;
  x(a: number, ...args: [...rest: number[], last: string]): boolean;
}
declare const r: R;
const a1: string = r.del('a');
const a2: string = r.del('a', 'b');
const a3: string = r.del(['a'], (e, v) => {});
const a4: string = r.del('a', (e, v) => { const q: string = v; });
const a5: string = r.mget('a', 'b');
const a6: string = r.mget('a', (e, v) => {});
const b1: string = r.x(1, 'a');
const b2: string = r.x(1, 2, 3, 'a');
const b3 = r.x(1, 2, 3);
const b4 = r.x(1, 'a', 'b');
const b5 = r.x(1);
