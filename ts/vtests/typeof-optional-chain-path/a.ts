// typeof a.b inside the optional chain a.b?.[...]: a.b isn't nullish there, so keyof gives its keys
declare const a: { b?: { x: number; y: string } | null };
declare const k: string;
export function f() {
  const v = a.b?.[k as keyof typeof a.b];
  const n: typeof v = true;
  const key = k as keyof typeof a.b;
  const kk: boolean = key;
}
