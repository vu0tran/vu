type OV = { [x: string]: any };
type RT<TD, TV extends OV, TC = 1> = [mutate: (v: TV) => TD, result: { d: TD; c: TC }];
type MRO<TV, TC> = TV;
declare function um<TD = unknown, TV extends OV = OV, TC = 1, TCV extends Partial<TV> = {}>(o?: TCV): RT<TD, MRO<TV, TCV>, TC>;
export const a: number = null! as ReturnType<typeof um>;
declare function um2<TD = unknown, TV extends OV = OV>(): RT<TD, TV>;
export const b: number = null! as ReturnType<typeof um2>;
