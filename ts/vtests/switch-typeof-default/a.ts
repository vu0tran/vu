// switch (typeof x): a default clause, or no case matching, narrows x to the members the other
// clauses' labels don't name (narrowTypeBySwitchOnTypeOf)
type V = boolean | number | string;
export const key = (value: V): string => {
  switch (typeof value) {
    case 'boolean':
      return `boolean:${value}`;
    case 'number':
      return `number:${value}`;
    case 'string':
      return `string:${value}`;
    default: {
      const ex: never = value;
      return ex;
    }
  }
};
export function f(v: number | string | (() => void) | undefined) {
  switch (typeof v) {
    case 'number': return 1;
    case 'function':
    default: { const e: string | (() => void) | undefined = v; if (e === 1) {} return e; }
  }
}
export function g(v: number | string | null) {
  switch (typeof v) {
    case 'number': return 1;
    case 'string': break;
  }
  const z: string | null = v; if (z === 1) {}
}
export function h(v: number | string | boolean) {
  switch (typeof v) {
    default: { const e: string | boolean = v; if (e === 1) {} return e; }
    case 'number': return 1;
  }
}
