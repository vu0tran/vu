export {};
declare function mk5(): { new (): { x: number; y?: string; z?: number; readonly w: 1 } & { x: 1; y: string; z?: number; w: number } };
class M5 extends mk5() {}
const m = new M5();
const a: string = m.x;
const b: number = m.y;
const c2: string = m.z;
m.w = 1;
m.x = 2;
