interface Ctx { timeout(n: number): void; name: string }
declare function before(fn: (this: Ctx) => Promise<void>): void;
before(async function () { this.timeout(5); const n: number = this; });
before(async function (this: Ctx) { const n: number = this.name; });
const original = {
  url: 'x',
  elementType: async function () { const n: number = this; },
  other: function () { return this.url; },
};
const o2 = { url: 'y', m() { const q: number = this.url; }, f: function () { const q: number = this.url; } };
interface Shape { area(): number; w: number }
const s: Shape = { w: 2, area: function () { const z: string = this.w; return 1; } };
declare function take(o: { f(this: Ctx): void }): void;
take({ f: function () { const z: number = this; } });
let mocha = require("mocha");
mocha.before(async function () {
  this.timeout(1000);
  const n: number = this;
});
function f() { return this.x; }
declare const g: any;
g((function () { const z: string = this; }));
declare function require(id: string): any;
