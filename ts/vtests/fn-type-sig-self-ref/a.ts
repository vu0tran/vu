type AnyFunc = (...args: any[]) => any;
type OmitLast<T> = T extends [...infer REST, any] ? REST : never;
type OmitLastParam<F extends AnyFunc> = (...args: OmitLast<Parameters<F>>) => ReturnType<F>;
type Next<IF, FN extends keyof IF> = Required<IF>[FN] extends AnyFunc ? OmitLastParam<Required<IF>[FN]> : never;
type Next2<IF, FN extends keyof IF> = IF[FN] extends AnyFunc ? OmitLastParam<IF[FN]> : never;
interface In { a: number }
interface Ic {
  execute?: (input: In, next: Next<Ic, 'execute'>) => Promise<unknown>;
}
export const x: Ic = {
  async execute(input, next) {
    const r: string = next(input);
    return next(input);
  },
};
