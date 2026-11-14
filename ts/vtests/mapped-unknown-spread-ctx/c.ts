type Awaitable<T> = T | PromiseLike<T>;
type MF<M = unknown> = (importOriginal: <T extends M = M>() => Promise<T>) => Awaitable<Partial<M>>;
declare function mock(path: string, factory?: MF): void;
mock('x', async (importActual) => {
  const r = await importActual();
  const n: number = r;
  return { ...(await importActual()) };
});
declare const io: <T extends unknown = unknown>() => Promise<T>;
async function g() { const q = { ...(await io()) }; }
export {};
const pu: Partial<unknown> = 1;
const pu2: Readonly<unknown> = 1;
const pu3: number = null as any as Partial<unknown>;
