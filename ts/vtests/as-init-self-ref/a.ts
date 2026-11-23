interface Ctx {
  result: string;
  flag?: boolean;
  go(): Promise<void>;
}
declare function check(a: unknown, b: unknown): void;
declare const opt: { x?: Error };

const make = () => {
  const fail = (): void => {
    if (opt.x) throw opt.x;
  };
  const doc = {
    result: '',
    flag: false,
    go: async () => {
      check(doc.result, '');
      const n: number = doc.result;
      fail();
    },
  } as unknown as Ctx;
  return doc;
};

interface C2 { result: string; go(): Promise<void>; }
const m1 = { result: '', go: async () => { const n: number = m1.result; } } as unknown as C2;
const m2 = { result: '', go: async () => { const n: number = m2.result; } } as C2;
const m4 = { result: '', go: () => { const n: number = m4.result; } } as unknown as C2;
const m5 = { result: '', go() { const n: number = m5.result; } } as unknown as C2;
const m6 = ({ inner: { go: () => { const n: number = m6.result; } } }) as unknown as C2;
