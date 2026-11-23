declare const w: any;
declare const s: string | number;
// The lib files are merged in tsgo's lib order (scripthost before es2015.core), so
// new (value: number | string | Date) is tried before new (vd: VarDate).
const d1: 0 = new Date(w);
const d2: 0 = new Date(s);
const vd: 0 = new Date(0).getVarDate();
type P = ConstructorParameters<DateConstructor>;
const p: 0 = null as unknown as P;
