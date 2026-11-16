// An evolving array earlier in the program: the loop's join doesn't compute the types of
// variables it hasn't reached yet (here `version`, outside the `if (n)` narrowing).
export function first() {
	const out = [];
	return out;
}

interface N { version: number | number[]; name: string }
declare function get(id: string): N | null;
declare function hint(id: string, v: number): string;

export function f(ids: string[], seen: Set<string>) {
	const lines: string[] = [];
	let count = 0;
	for (const id of ids) {
		const n = get(id);
		if (n) {
			const version = Array.isArray(n.version) ? n.version[n.version.length - 1] : n.version;
			const h = hint(id, version);
			const parts = [`${n.name} ${version}`];
			if (h) parts.push(h);
			lines.push(parts.join("\n"));
			seen.add(id);
			count++;
		}
	}
	return count + lines.length;
}
