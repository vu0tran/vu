// discriminants and predicates over intersections and unions of predicate methods
export {};
interface ET { type: 'text'; text: string; ok?: false }
interface EC { type: 'code'; text: string }
type PC = EC & { parsed: number; ok: true };
function q(c: ET | PC) {
	switch (c.type) { case 'code': { const m: number = c; break; } default: { const m: number = c; } }
	if (c.ok) { const m: number = c; } else { const m: number = c; }
}
