// a homomorphic mapped type over a type with a string index signature only: that index signature, not keyof's number too (forEachMappedTypePropertyKeyTypeAndIndexSignatureKeyType), with an as clause too (apollo's MakeRequiredVariablesOptional)
type S<T> = { [K in keyof T]: T[K] } & {};
type Q<T> = { [K in keyof T as K]: T[K] };
declare const r2: S<Q<Record<string, any>>>;
const n2: number = r2;
type Q3<T> = { [K in keyof T as K extends string ? K : never]: T[K] };
declare const r4: S<Q3<Record<string, any>>>;
const n4: number = r4;
declare const r5: S<Q<Record<number, any>>>;
const n5: number = r5;
