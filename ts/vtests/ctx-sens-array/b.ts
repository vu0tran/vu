interface Base { id: string; v?: string }
interface WB extends Base { extra: 1 }
type R<W> = (prev: W) => boolean;
declare const ws: WB[];
declare function g1<W extends Base>(ws: W[], skip: Array<R<W>>): W[];
g1(ws, [(prev) => prev.v === ""]);
declare function g2<W extends Base>(ws: W[], skip: R<W>): W[];
g2(ws, (prev) => prev.v === "");
declare function g3<W extends Base>(ws: W[], skip: Array<(prev: W) => boolean>): W[];
g3(ws, [(prev) => prev.v === ""]);
declare function g4<W>(ws: W[], skip: Array<(prev: W) => boolean>): W[];
g4(ws, [(prev) => true]);
declare function g5<W>(ws: W[], skip: ((prev: W) => boolean)[]): W[];
g5(ws, [(prev) => true]);
export {};
