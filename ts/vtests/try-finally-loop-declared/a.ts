// a variable assigned in a loop in a try block, read in its finally block: where the states known
// there already make its declared type, that's its type (a package's chat service)
export {};
declare function next(): Promise<number>;
export async function f(signal: { aborted: boolean }) {
  let pending: Promise<number> | undefined;
  try {
    while (!signal.aborted) {
      pending ??= next();
      await pending;
      if (Math.random()) pending = undefined;
    }
  } finally {
    await pending?.catch(() => 0);
    pending.then;
  }
}
