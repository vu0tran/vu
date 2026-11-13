type GV = string | number | boolean | object | null | undefined;
interface DO { [k: string]: GV | DO | DO[] }
declare function count(s: string): number;
declare const p: { sendBody?: boolean; jsonBody?: string } | undefined;
export function f(item: { tool?: DO }) {
  if (!item.tool) item.tool = {};
  item.tool.url = 'x';
  item.tool.n = 0;
  item.tool.n += count('a');
  if (p?.sendBody) {
    item.tool.b = true;
    if (p?.jsonBody) {
      item.tool.n += count(p.jsonBody);
    }
  }
}
