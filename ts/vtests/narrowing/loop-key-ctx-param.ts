type Item = { operation?: string; resource?: string; mode?: string; x: number };
declare function get(): { [k: string]: unknown } | null;
export function f(item: Item, nodes: string[]) {
  for (const n of nodes) {
    if (n === 'a') {
      item.x = 1;
    } else {
      try {
        const ps = get();
        if (ps) {
          const keys: Array<'operation' | 'resource' | 'mode'> = ['operation', 'resource', 'mode'];
          keys.forEach((key) => {
            if (ps.hasOwnProperty(key)) {
              item[key] = ps[key]?.toString();
            }
          });
        }
      } catch (e) {}
    }
  }
}
