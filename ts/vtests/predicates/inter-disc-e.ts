// discriminants and predicates over intersections and unions of predicate methods
export {};
interface Type<T> { check(value: any, deep?: any): value is T }
interface SW { kind: 's'; discriminant: number }
interface IF { kind: 'i' }
declare const n: { SwitchStatement: Type<SW> };
function f(region: SW | IF) {
	if (n.SwitchStatement.check(region)) { const m: string = region.discriminant; }
	const ok = !(n.SwitchStatement.check(region) && region.discriminant === 1);
}
