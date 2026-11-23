// an interface property declared unique symbol: its own symbol type (OpTypes["notIn"]), keying
// properties named by it, as sequelize's Op
interface OpTypes { readonly notIn: unique symbol; readonly eq: unique symbol }
declare const Op: OpTypes;
type W = { v?: { [Op.notIn]: number[] } };
declare const w: W;
const a: string = w.v![Op.notIn];
const b: string = Op.notIn;
const c: { [Op.eq]: 1 } = { [Op.eq]: 1 };
const d: string = c[Op.eq];
// typeof a.b with no value a: TS2304 and the error type
type F = ReturnType<typeof vq.fn>;
const f: F = 1;
