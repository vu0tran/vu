function f1(): never { throw 1; }
function f2(): never { while (true) {} }
function f3(): never { for (;;) {} }
function f4(x: boolean): never { if (x) throw 1; else throw 2; }
function f5(x: number): never { switch (x) { case 1: throw 1; default: throw 2; } }
function f6(): never { do { } while (true); }
function f7(x: boolean): never { while (true) { if (x) break; } }
async function f8(): Promise<never> { throw 1; }
async function f9(): Promise<never> { await 1; }
const f10 = (): never => { throw 1; };
const f11 = (): never => { };
function f12(): never { try { throw 1; } finally { } }
function f13(): never { try { } catch { throw 1; } }
function f14(): never { lbl: while (true) { continue lbl; } }
function f15(): never { while (1) {} }
class C { m(): never { throw 1; } n(): never { this.m(); } }
export {};
