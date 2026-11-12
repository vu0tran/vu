export type JsonValue = string | number | boolean | null | JsonObject | JsonValue[];
export type JsonObject = { [key: string]: JsonValue };
declare function parse<T = JsonObject>(s: string): T;
export const j: number = parse("x");
declare function id<T>(x: T): T;
export const k: number = id(parse("y") as JsonValue);
export function g<T extends JsonValue>(v: T): T { return v; }
export const m: number = g(1 as JsonValue);
