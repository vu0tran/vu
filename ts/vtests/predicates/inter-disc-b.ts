// discriminants and predicates over intersections and unions of predicate methods
export {};
interface ET { type: 'text'; text: string }
interface EC { type: 'code'; text: string }
type PC = EC & { parsed: number };
declare const chunks: (ET | PC)[];
const r = chunks.filter((c) => c.type === 'code').some((c) => c.parsed > 1);
declare const x: ET | PC;
if (x.type === 'code') { const n: string = x; } else { const n: string = x; }
