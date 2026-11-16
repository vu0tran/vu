interface Arg { key: string }
declare const args: Arg[];
const obj = args.reduce((acc: Record<string, number>, a) => { acc[a.key] = 1; return acc; }, {});
export const n: string = obj;
