// An intersection source's property optional in every member that has it, against a required
// target property: not assignable (propertiesRelatedTo), and so not `extends` it either (React's
// ReactManagedAttributes<C, P> reads C extends { propTypes: infer T } for C with propTypes?: any).
interface P { value: Date | null; onChange?: (v: Date | null, n: number) => void }
declare const x1: { a: 1 } & { p?: any };
const y1: { p: any } = x1;
declare const x2: { a: 1 } & { p?: number };
const y2: { p: number | undefined } = x2;
declare const x3: { a: 1 } & { p?: number } & { p: number };
const y3: { p: number } = x3;
type F = (p: P) => number;
type Q3 = (F & { propTypes?: any }) extends { propTypes: infer T } ? T : 'no';
const q3: null = null as any as Q3;
type Q4 = (F & { propTypes?: any }) extends { propTypes: any } ? 'yes' : 'no';
const q4: null = null as any as Q4;
type Q6 = ({ a: 1 } & { p?: number }) extends { p?: number } ? 'yes' : 'no';
const q6: null = null as any as Q6;
declare const x4: { a: 1 } & { p?: number };
const c4 = x4 as { p: number };
