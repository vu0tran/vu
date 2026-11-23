// string & {}: a mapped type over it has a string index signature, so the type isn't weak
type MT = 'application/json' | 'text/html' | (string & {});
type CO = Partial<Record<MT, { schema: number }>>;
export const a: CO = { 'multipart/form-data': { schema: 1 } };
export const b: CO = { 'multipart/form-data': { schema: "x" } };
export const c: Record<string & {}, number>['k'] = "s";
