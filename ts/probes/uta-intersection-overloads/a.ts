// screen.getByRole of @testing-library/dom: a generic method intersected with a mapped type's
// bound function; the call takes the generic one (reorderCandidates), T from the assertion
type G<T extends HTMLElement = HTMLElement> = (container: HTMLElement, role: string) => T;
type BF<F> = F extends (container: HTMLElement, ...args: infer P) => infer R ? (...args: P) => R : never;
declare function getByRole<T extends HTMLElement = HTMLElement>(container: HTMLElement, role: string): T;
declare const queries: { getByRole: typeof getByRole };
type Bound<Q> = {
  getByRole<T extends HTMLElement = HTMLElement>(...args: Parameters<BF<G<T>>>): ReturnType<G<T>>;
} & { [P in keyof Q]: BF<Q[P]> };
declare const screen: Bound<typeof queries>;
export const b = screen.getByRole('button') as HTMLButtonElement;
export const c = (screen.getByRole('searchbox') as HTMLInputElement).value;
type S = { get<T extends HTMLElement = HTMLElement>(role: string): T } & { get: (role: string) => HTMLElement };
declare const s: S;
export const d = s.get('b') as HTMLButtonElement;
export const e = s.get('b') as HTMLElement;
