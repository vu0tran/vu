// discriminants and predicates over intersections and unions of predicate methods
export {};
interface ET { type: 'text'; text: string }
interface EC { type: 'code'; text: string }
type PC = EC & { parsed: number };
const isP = (c: ET | PC) => c.type === 'code';
const n: number = isP;
function q(c: ET | PC) { if (c.type === 'code') {} else { const m: number = c; } }
