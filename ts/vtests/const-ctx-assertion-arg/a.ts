declare function init<const T extends { model: string }>(c: { cfg: T; n?: number }): T;
const a = init({ cfg: { model: 'x' } });
const n1: number = a;
const b = init({ cfg: { model: 'y' } } as never);
const n2: string = b;
export {};
