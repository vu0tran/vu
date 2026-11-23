// a spread of a union of object types and {} with nothing before it: the union of the spreads,
// checked (printing it is what isn't modeled: b.ts)
declare function call(o: { url: string; a?: string; b?: string }): void;
const cases = [{}, { a: 'x', b: 'y' }, { a: 'x' }];
for (const scope of cases) call({ ...scope, url: 'u' });
export const n: string = 1;
