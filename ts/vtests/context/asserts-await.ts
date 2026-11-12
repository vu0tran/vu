export function assert(condition: unknown, message?: string): asserts condition {
  if (!condition) throw new Error(message ?? "x");
}
export async function s1(): Promise<void> {
  return await new Promise((resolve) => { resolve(); });
}
export async function s2(): Promise<void> {
  return new Promise((resolve) => { resolve(); });
}
export function s3(): Promise<void> {
  return new Promise((resolve) => { resolve(); });
}
