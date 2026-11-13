type GV = string | number | boolean | object | null | undefined;
interface DO { [k: string]: GV | DO | DO[] }
declare function count(s: string): number;
export function f(item: { tool: DO }, c: boolean) {
  item.tool.n = 0;
  item.tool.n += count('a');
  item.tool.n += count('b');
  if (c) { item.tool.n += 1; }
  { item.tool.n += 1; }
}
