// (an array literal for readonly [...T], T a const type parameter: in a const context; a callback
// beside it whose return type is another type parameter: not in one)
type NonNullableTuple<T extends readonly unknown[]> = { [K in keyof T]: NonNullable<T[K]> };
declare function mapDefinedValues<const T extends readonly unknown[]>(values: readonly [...T]): NonNullableTuple<T> | false;
declare function mapDefinedValues<const T extends readonly unknown[], R>(values: readonly [...T], fn: (...args: NonNullableTuple<T>) => R, defaultValue: R): R;
declare const a: number | null;
declare const b: string | undefined;
const t1 = mapDefinedValues([a, b], (x, y) => x + y.length, a);
const t2 = mapDefinedValues([a, b]);
const t3 = mapDefinedValues([1, "s"]);
const n1: string = t1;
const n2: string = t2;
const n3: string = t3;
const t4 = mapDefinedValues([{ a: 1 }, [2, "x"]]);
const n4: string = t4;
declare function tup<const T extends readonly unknown[]>(v: [...T]): T;
const t5 = tup([1, { b: [true] }]);
const n5: string = t5;
declare function cb<const T extends readonly unknown[], R>(v: readonly [...T], f: () => R): [T, R];
const t6 = cb([1], () => ({ z: 1 }));
const n6: string = t6;
export {};
