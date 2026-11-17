export {};
const base = { q: 1 };
const a = [{ x: 1 }, { ...base, y: 2 }];
const n2: number = a[1].x;
const b = [{ d: { x: 1 } }, { d: { ...base, y: 2 } }];
const n4: number = b[1].d.x;
const c = [{ d: { x: 1 } }, { ...base, d: { y: 2 } }];
const n6: number = c[0].d.y;
const n7: number = c[1].d.x;
