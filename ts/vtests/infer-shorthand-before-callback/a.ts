// a shorthand property's type inferred from before a context-sensitive callback beside it
class M { x = 1; get(): string { return ''; } }
interface I { get(): string }
declare function plan<T>(a: { markers: readonly T[]; tokenOf: (marker: T) => string | undefined }): T[];
declare const ms: M[];
declare const is: I[];
const p1 = plan({ markers: ms, tokenOf: (marker) => marker.get() });
const n1: number = p1;
const p2 = plan({ markers: ms, tokenOf: (marker: M) => marker.get() });
const n2: number = p2;
const markers = is;
const p3 = plan({ markers, tokenOf: (marker) => marker.get() });
const n3: number = p3;
declare function plan2<T>(markers: readonly T[], tokenOf: (marker: T) => string | undefined): T[];
const p4 = plan2(ms, (marker) => marker.get());
const n4: number = p4;
