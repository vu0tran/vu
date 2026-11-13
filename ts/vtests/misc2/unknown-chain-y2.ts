interface G { operation?: string; resource?: string; mode?: string; other: number }
declare const p: { [k: string]: unknown } | undefined;
export function f(item: G) {
  if (p) {
    const keys: Array<'operation' | 'resource' | 'mode'> = ['operation', 'resource', 'mode'];
    keys.forEach((key) => {
      if (p.hasOwnProperty(key)) {
        item[key] = p[key]?.toString();
      }
    });
  }
}
