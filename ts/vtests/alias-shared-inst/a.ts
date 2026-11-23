type OperationVariables = Record<string, any>;
type ClassDictionary = Record<string, any>;
interface R<V> { v: V }
declare const a: R<OperationVariables>;
declare const b: R<ClassDictionary>;
declare const c: R<Record<string, any>>;
const n1: number = a;
const n2: number = b;
const n3: number = c;
type P1 = Partial<{ x: number }>;
declare const p1: P1;
const n4: number = p1;
declare function f<T extends OperationVariables = OperationVariables>(x: T): R<T>;
declare function f<T extends OperationVariables = OperationVariables>(x: T, y: number): R<T>;
declare const rt: ReturnType<typeof f>;
const n5: number = rt;
const ok: OperationVariables = {} as ClassDictionary;
