interface O { a?: string; b?: number; c: boolean }
declare function expects<K extends keyof O>(obj: O, ...keys: K[]): asserts obj is O & { [P in K]: NonNullable<O[P]> };
export function f(options: O) {
  if (options.c) {
    expects(options, 'a');
    const z: 'z' = options.a;
  }
  const y: 'z' = options.a;
}
