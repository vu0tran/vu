type Awaitable<T> = T | PromiseLike<T>;
interface EachFunctionReturn<T extends any[]> {
  (name: string | Function, fn: (...args: T) => Awaitable<void>, options?: number): void;
}
type ExtractEachCallbackArgs<T extends ReadonlyArray<any>> = {
  1: [T[0]];
  2: [T[0], T[1]];
  fallback: Array<T extends ReadonlyArray<infer U> ? U : any>;
}[T extends Readonly<[any]> ? 1 : T extends Readonly<[any, any]> ? 2 : 'fallback'];
interface TestEachFunction {
  <T extends any[] | [any]>(cases: ReadonlyArray<T>): EachFunctionReturn<T>;
  <T extends ReadonlyArray<any>>(cases: ReadonlyArray<T>): EachFunctionReturn<ExtractEachCallbackArgs<T>>;
  <T>(cases: ReadonlyArray<T>): EachFunctionReturn<T[]>;
}
declare const each: TestEachFunction;
each([
  { outcome: 'UnauthorizedError', failure: 'forbidden' },
  { code: 'UNAUTHENTICATED', failure: 'signedOut' },
  { status: 401, failure: 'signedOut' },
] as const)('x', async (denial) => {
  if (denial.outcome !== undefined) {
    const o: number = denial.outcome;
  }
});
