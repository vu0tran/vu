declare class IM { a: number; b?: string }
declare class SR<Q extends IM = IM> { q: Q; c?: number }
type RL<A extends typeof IM = typeof IM, B extends typeof SR<InstanceType<A>> = typeof SR> = (req: InstanceType<A>, res: InstanceType<B> & { req: InstanceType<A> }) => void;
declare function k(x?: RL<typeof IM, typeof SR>): 1;
declare function k(o: {}, x?: RL<typeof IM, typeof SR>): 2;
export const r: 1 = k((_, res) => { res.q.a; });
declare const l2: (_: IM) => void;
export const r2: 1 = k(l2);
