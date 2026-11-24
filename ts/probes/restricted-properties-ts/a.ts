import * as ns from "./m";
class A extends ns.Base implements ns.Iface, ns.Other {
  @ns.deco foo = 1;
  #bar = 2;
  m() { return this.#bar + this.bar + super.bar; }
}
interface I extends ns.Iface {}
const t: typeof ns.value = ns?.value;
const u = (ns as any).value + (ns!).value + (<any>ns).value;
ns["value"]; ns[`value`]; ns[1.5]; ns[1e21]; ns[0x10]; ns[10n]; ns[0x10n]; ns[-1]; ns[("value")];
({ value: ns.x, [ns.k]: v0 } = ns);
({ value } = ns);
({ "value": v1, 1: v2, [value]: v3, ["value"]: v4 } = ns);
[{ value: v5 }] = ns;
for ({ value } of list) {}
for (const { value } of list) {}
function f({ value } = ns, [{ value: w }] = ns) {}
const { value: z1, ...rest } = ns, { ["value"]: z2 } = (ns as any);
try {} catch ({ value }) {}
export = ns.value;
let q = ns.value?.(ns.value);
ns.value++;
delete ns.value;
const ob = { value: 1 }.value;
