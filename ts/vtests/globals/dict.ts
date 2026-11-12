interface Dict<T> { [key: string]: T | undefined }
interface PE extends Dict<string> { TZ?: string }
declare const pe: PE;
export const a: number = pe.FOO;
export const b: number = pe["HOME"];
namespace NS { export interface D2<T> { [key: string]: T | undefined } export interface P2 extends D2<string> { TZ?: string } }
declare const p2: NS.P2;
export const c: number = p2.X;
