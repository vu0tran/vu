// a lib a file references (/// <reference lib="dom" />, as @types/jsdom does): loaded with the
// other libs, before every other file; a var declared again in a declaration file isn't checked
// with skipLibCheck (the worker types' Request, lib.dom's too)
/// <reference lib="dom" />
declare var Request: { prototype: Request; new (input: string): Request };
