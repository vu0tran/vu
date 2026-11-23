declare function ev<R>(f: (x: Record<string, string>) => R, a: Record<string, string>): Promise<R>;
export const resolveFields = async <T extends Record<string, string>>(labels: T): Promise<Record<keyof T, string>> => {
  const { found, missing } = (await ev((labelMap: Record<string, string>) => {
    const found: Record<string, string> = {};
    const missing: string[] = [];
    return { found, missing };
  }, labels)) as { found: Record<keyof T, string>; missing: string[] };
  const n: number = found;
  return found;
};
export function g<T extends Record<string, string>>(r: Record<string, string>, s: Record<keyof T, string>) {
  const a = r as Record<keyof T, string>;
  const b: Record<keyof T, string> = r;
  const c: Record<string, string> = s;
  const d = 1 as unknown as Record<keyof T, string>;
}
