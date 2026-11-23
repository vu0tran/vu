// a function declaration returning no value is void without its body: a callback passed to the call
// whose result it reads calls it (react-hook-form's form, reset destructured from it)
declare function useThing(o: { onDone: () => void }): { form: { reset(): void; n: number } };
export function Comp(close: (b: boolean) => void) {
  const { form } = useThing({
    onDone: () => {
      handle(false);
    },
  });
  const { reset, n } = form;
  const s: string = n;
  function handle(next: boolean) {
    if (!next) reset();
    close(next);
  }
  return form;
}
export function g(x: number) { const y: string = x; }
export async function h(x: number) { const y: string = x; }
export const v: number = g(1);
export const w: number = h(1);
