// A function inside a callback in the initializer of a variable whose type is being found, passed
// to a call there: its body is checked once the variable has its type (tsc checks function bodies
// deferred), so the variable isn't any in it.
declare function take(f: () => void): void;
export const f = (inputs: string[]) => {
  const listeners = inputs.map((signal) => {
    const onAbort = () => {
      for (const [input] of listeners) {
        const q: number = input;
      }
    };
    take(onAbort);
    return [signal, onAbort] as const;
  });
  return listeners;
};
export const g = (inputs: AbortSignal[]) => {
  const ls = inputs.map((signal) => {
    const onAbort = () => {
      for (const [input, listener] of ls) input.removeEventListener('abort', listener);
      const n: number = signal;
    };
    signal.addEventListener('abort', onAbort);
    return [signal, onAbort] as const;
  });
  return ls;
};
