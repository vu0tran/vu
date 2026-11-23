// A function in a variable's initializer whose inferred return type reads that variable (vitest's
// vi.hoisted): read while the variable's type is being found, it's any there, but the body is
// checked again once the variable has its type, as tsc checks it.
declare function hoisted<T>(f: () => T): T;
const flagState = hoisted(() => {
  const evaluator = async (_flag: string) => { const q: string = flagState.enabled; return flagState.enabled; };
  const other = (x: number) => { const q: string = flagState.enabled; return x; };
  return { enabled: false, evaluator, other };
});
const r: number = flagState.enabled;
// (a function reading itself, before and after its declaration)
export function outer(pending: boolean, once: (f: () => void) => void) {
  const cancel = () => {
    if (!pending) return;
    once(complete);
  };
  const complete = () => {
    if (!pending) return;
    const s9: string = complete;
    once(complete);
  };
  cancel();
}
