// a generic target signature seen through an instantiation (react-hook-form's UseFormSetValue<Data>): its type parameter's constraint instantiated, a template literal type of the data's keys
type SetValue<TV> = <TN extends `${keyof TV & string}`>(name: TN, value: TV[TN & keyof TV]) => void;
type D = { a: string; b: number };
declare const sv: SetValue<D>;
declare const sa: (v: { x: 1 } | null) => void;
const arr = [sa, sv];
const n: number = arr;
declare const sb: (v: string) => void;
const arr2 = [sb, sv];
const n2: number = arr2;
