// a package's useToast exactly: Partial<Pick<O, Extract<keyof D, keyof O>>> spread from a union with
// undefined: the keys' lower bound, the literal keys of D's constraint that O has
export {};
type ToastOptions = { type: 'error' | 'info'; message: string; description?: string; analyticsName: string; openDelayMs?: number };
type ShowToastArg<D extends Partial<ToastOptions>> = Omit<ToastOptions, keyof D> &
  Partial<Pick<ToastOptions, Extract<keyof D, keyof ToastOptions>>>;
export function use<D extends Partial<ToastOptions>>(defaults?: D) {
  const ref = { current: defaults };
  return (...args: {} extends ShowToastArg<D> ? [options?: ShowToastArg<D>] : [options: ShowToastArg<D>]) => {
    const merged = { ...ref.current, ...args[0] } as ToastOptions;
    const n: number = merged;
  };
}
