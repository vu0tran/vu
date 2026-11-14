namespace objectUtil {
  type optionalKeys<T extends object> = { [k in keyof T]: undefined extends T[k] ? k : never }[keyof T];
  type requiredKeys<T extends object> = { [k in keyof T]: undefined extends T[k] ? never : k }[keyof T];
  export type addQuestionMarks<T extends object, _O = any> = {
    [K in requiredKeys<T>]: T[K];
  } & {
    [K in optionalKeys<T>]?: T[K];
  } & { [k in keyof T]?: unknown };
  export type identity<T> = T;
  export type flatten<T> = identity<{ [k in keyof T]: T[k] }>;
}
type RawShape = { [k: string]: ZT };
type UKP = "passthrough" | "strict" | "strip";
declare abstract class ZT<Output = any> {
  readonly _output: Output;
  parse(data: unknown): Output;
}
type baseOut<Shape extends RawShape> = { [k in keyof Shape]: Shape[k]["_output"] };
type CatchallOutput<T extends ZT> = ZT extends T ? unknown : { [k: string]: T["_output"] };
type PassthroughType<T extends UKP> = T extends "passthrough" ? { [k: string]: unknown } : unknown;
type objOut<Shape extends RawShape, Catchall extends ZT, UnknownKeys extends UKP = UKP> = objectUtil.flatten<objectUtil.addQuestionMarks<baseOut<Shape>>> & CatchallOutput<Catchall> & PassthroughType<UnknownKeys>;
declare class ZO<T extends RawShape, UnknownKeys extends UKP = UKP, Catchall extends ZT = ZT, Output = objOut<T, Catchall, UnknownKeys>> extends ZT<Output> {
  get shape(): T;
}
type Infer<T extends ZT> = T["_output"];
type CI<Flags extends RawShape> = { fs?: ZO<Flags> };
function f<Flags extends RawShape>(inp: CI<Flags>) {
  let flags = {} as Infer<ZO<Flags>>;
  if (inp.fs) flags = inp.fs.parse(1);
}
export {};
