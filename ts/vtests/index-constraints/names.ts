export {};
interface A { [k: string]: string; "abc": 1; 'q': 2; "3": 3; 4: 4 }
function h<K extends string>(m1: { [P in K]?: number }, m2: { [P in K]?: number | undefined }, m3: { [P in K]-?: number | undefined }, m4: { +readonly [P in K]+?: string }) {
	const b1: boolean = m1; const b2: boolean = m2; const b3: boolean = m3; const b4: boolean = m4;
}
