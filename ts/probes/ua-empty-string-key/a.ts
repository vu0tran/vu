// An object literal's '' key is a named key: the contextual type's property or index signature.
declare const anyv: any;
export const gates: Record<string, Promise<void>> = { '': Promise.resolve(), b: Promise.resolve() };
export const loose: Record<string, unknown> = { '': anyv };
export const strict: { '': number } = { '': anyv };
export const none = { '': anyv };
