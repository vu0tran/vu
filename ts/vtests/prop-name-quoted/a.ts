const o = {"n": 1};
const p: typeof o = {};
interface I { "x": number; y: number }
const q: I = { y: 1 };
const r: I = {};
const o2 = {"n": 1, ["m"]: 2, 3: 4, "4": 5};
const p2: typeof o2 = {};
export {};
