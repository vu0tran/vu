type Fn = () => null;
/** @deprecated Old type. */
export type Fn2 = () => null;
/** @deprecated Old fn type. */
type Fn3 = (a: number) => number;
export const viaAlias: Fn3 = (a) => a;
export const destructured = { run: (a: number) => a };
/**
 * @deprecated Use taskGroups instead.
 */
export const tasks: Fn = () => null;
export const agent: Fn = () => null;
/** @deprecated Prefer other. */
export const escalate: Fn = async () => null as never;
