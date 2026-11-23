// an await in a generic call's argument whose parameter is InputByType[T] | Promise<InputByType[T]>
// (jszip's file): the operand gets no contextual type here, the call infers T from it
export {};
interface InputByType { text: string; buf: ArrayBuffer }
type InputType = keyof InputByType;
declare function file<T extends InputType>(p: string, data: InputByType[T] | Promise<InputByType[T]>): T;
declare function getBuf(): Promise<ArrayBuffer>;
export async function f() {
  const k = file('a', await getBuf());
  const s: InputType = k;
  const k2 = file('b', await Promise.resolve('x'));
  const z: number = "x";
}
