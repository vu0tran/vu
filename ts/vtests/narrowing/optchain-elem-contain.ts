declare const pairs: [number, (a: number) => boolean][];
declare const score: number;
const smallest = pairs.at(-1);
export const r = smallest?.[0] === score ? smallest[1](1) : false;
export const r2 = smallest?.[0] !== undefined ? smallest[1](1) : false;
