// an anonymous function is named by the variable it initializes, its property key, or the name it is assigned to
declare const b: boolean;
export const f1 = (): number | undefined => { if (b) return; return 1; };
export const f2 = async () => { if (b) return; return 1; };
export const f3 = function () { if (b) return; return 1; };
export const f4 = function named() { if (b) return; return 1; };
export const o = { p1: () => { if (b) return; return 1; }, p2() { if (b) return; return 1; }, p3: function () { if (b) return; return 1; } };
let f5: () => number | undefined;
f5 = () => { if (b) return; return 1; };
export class C { m = () => { if (b) return; return 1; }; static s = () => { if (b) return; return 1; } }
export default () => { if (b) return; return 1; };
export const f6 = (x: number) => [1].map(() => { if (b) return; return x; });
