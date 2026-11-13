type BR = ReturnType<any[][typeof Symbol.iterator]> extends globalThis.Iterator<any, infer TReturn> ? TReturn : any;
export const b: 'z' = null as unknown as BR;
