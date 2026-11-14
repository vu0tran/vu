type Awaitable<T> = T | PromiseLike<T>;
type MF<M = unknown> = (importOriginal: <T extends M = M>() => Promise<T>) => Awaitable<Partial<M>>;
interface Opts { spy?: boolean }
declare const vi: {
  mock(path: string, factory?: MF | Opts): void;
  mock<T>(module: Promise<T>, factory?: MF<T> | Opts): void;
};
vi.mock('x', async (importActual) => ({
  ...(await importActual()),
  S3: 1,
}));
export {};
