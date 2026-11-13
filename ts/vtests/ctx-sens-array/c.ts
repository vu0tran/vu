interface Base { id: string; v?: string }
interface WB extends Base { extra: 1 }
declare const ws: WB[];
declare const flag: boolean;
declare function g1<W extends Base>(ws: W[], f: (p: W) => boolean): W[];
g1(ws, flag ? (p) => p.extra === 1 : (p) => p.v === "");
g1(ws, flag || ((p) => p.extra === 1));
declare const maybe: ((p: WB) => boolean) | undefined;
g1(ws, maybe ?? ((p) => p.extra === 2));
declare function g2<W extends Base>(ws: W[], f: { run: (p: W) => boolean }[]): W[];
g2(ws, [{ run: (p) => p.extra === 1 }, { run: (p) => p.nope === 1 }]);
declare function g3<W extends Base>(ws: W[], f: ((p: W) => boolean)[][]): W[];
g3(ws, [[(p) => p.extra === 1], [(p) => p.nope]]);
declare function g4<W extends Base>(f: ((p: W) => boolean)[], ws: W[]): W[];
const r4: string = g4([(p) => p.extra === 1], ws);
declare function g5<T>(xs: T[], fs: ((x: T) => void)[]): T;
const r5: string = g5([1, 2], [(x) => { const y: string = x; }]);
declare function g6(x: number, fs: ((a: number) => void)[]): void;
declare function g6(x: string, fs: ((a: string) => void)[]): void;
g6("s", [(a) => { const n: number = a; }]);
export {};
