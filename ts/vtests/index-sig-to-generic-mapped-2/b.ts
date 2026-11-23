declare const numIdx: { [n: number]: string };
// (a number index signature's key stays: related where the keys are numbers)
export function n1<T extends number>(): Record<T, string> { return numIdx; }
export function n2<T extends string>(): Record<T, string> { return numIdx; }
export function n3<T extends number>(): Partial<Record<T, string>> { return numIdx; }
