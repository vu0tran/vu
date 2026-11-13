// spreads of falsy-or-object unions (cond && {...}), and of types that aren't objects
export {};
declare const b: boolean;
declare const u: undefined;
declare const nu: null | undefined;
const a1 = { ...u };
const a2 = { ...nu };
const a3 = { ...(b && null) };
const a4 = { ...false };
const a5 = { ...(b && undefined) };
const a6 = { ...0 };
const a7 = { ...(b as false | undefined) };
