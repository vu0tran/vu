type P = { category: "a" | "b"; n: number };
export const f1: () => P = () => ({ category: "a", n: 1 });
export const f2: () => P = () => { return { category: "a", n: 1 }; };
export const f3: () => P = function () { return { category: "a", n: 1 }; };
export const f4: () => "a" | "b" = () => "a";
export const f5: () => { c: "a" } = () => ({ c: "a" });
export const o: P = { category: "a", n: 1 };
