declare function take(s: string): void;
declare function other(): { name: string };
export const o = {
  $: (nodeName?: string) => {
    if (!nodeName) {
      nodeName = other().name;
      if (!nodeName) throw new Error('x');
    }
    take(nodeName);
    const f = () => take(nodeName);
    return new Proxy({}, {
      get(target, property) { take(nodeName); return target; },
    });
  },
};
declare const maybe: string | undefined;
if (maybe) {
  const ob = { m() { take(maybe); }, get g() { take(maybe); return 1; } };
  class K { m() { take(maybe); } }
  console.log(ob, K);
}
