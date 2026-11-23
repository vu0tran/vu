// TypeScript 6: an inference from the return type alone that doesn't meet the constraint keeps the
// members of it that do (filteredByConstraint), so useCallback's T extends Function from
// ((e: E) => void) | undefined gives the callback its parameter types.
declare function uc<T extends Function>(callback: T, deps: unknown[]): T;
declare function uo<T extends { a: 1 }>(callback: T, deps: unknown[]): T;
type E = { key: string };
export const h1: ((e: E) => void) | undefined = uc((event) => {
  const n: number = event;
}, []);
export const h2: ((e: E) => void) | string = uc((event) => {
  const n: number = event;
}, []);
export const h3: number = uc((event) => {
  const n: number = event;
}, []);
export const h4: ((e: E) => void) | undefined = uo((event) => {
  const n: number = event;
}, []);
declare const u: ((e: E) => void) | undefined;
export const h5 = uc(u, []);
