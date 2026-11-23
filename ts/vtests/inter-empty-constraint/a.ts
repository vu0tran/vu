// T & {} with T's constraint {} (or {} | undefined) is T, not never (getIntersectionType:
// isTypeStrictSubtypeOf({}, {})): pothos's ExtendDefaultTypes' Inputs: PartialTypes['Inputs'] & {}
interface U { Inputs: {}; Objects: {} }
interface E<P extends Partial<U>> { Inputs: P['Inputs'] & {} }
type F<Param> = Param extends keyof E<{}>['Inputs'] ? 'yes' : 'no';
export const c: F<'Inner'> = 1;
type Mc<P extends { Inputs: {} }> = P['Inputs'] & {};
declare const x: Mc<{ Inputs: { a: 1 } }>;
export const b3: number = x;
