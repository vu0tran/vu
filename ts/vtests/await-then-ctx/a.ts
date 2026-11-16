// Inferring from a generic signature to a generic one: the target's own type parameters are erased.
declare function jsonParse<T>(s: string): T | undefined;
declare function readFile(p: string): Promise<string>;
export async function readPackageName(): Promise<string> {
	return await readFile('package.json').then((pj) => jsonParse<{ name: string }>(pj)?.name ?? 'unknown');
}
export async function b(): Promise<string> {
	const x = await readFile('a').then((pj) => pj + "1");
	return x;
}
export async function c(): Promise<string> {
	return await readFile('a').then((pj) => pj);
}
