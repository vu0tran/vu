interface Tr { start<T>(o: string, run: (s: number) => Promise<T>): Promise<T> }
export const t: Tr = {
  async start(_o, run) { return await run(1); },
};
export async function f<T>(run: () => Promise<T>): Promise<T> {
  const v = await run();
  return v;
}
export async function g<T>(run: () => Promise<T>): Promise<T> {
  return run();
}
export async function h<T>(x: T): Promise<T> {
  return x;
}
