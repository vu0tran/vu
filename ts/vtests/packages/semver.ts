import { coerce, VERSION } from "semverish";
export const c: number = coerce("1");
export const v: number = VERSION;
declare const u: unknown;
export const b: string = FakeBuffer.isFakeBuffer(u) ? u.byteLength : "";
