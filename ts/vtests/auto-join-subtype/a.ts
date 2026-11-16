// let x; without a type: the join of its assignments reduces by subtypes.
interface ICred { [key: string]: string | number }
declare function getData(): Promise<ICred>;
export async function f(key: string, data: string) {
	let fullData;
	try {
		fullData = await getData();
	} catch (e) {
		fullData = {};
	}
	fullData[key] = data;
	const n: number = fullData;
	return fullData;
}
export function g(b: boolean) {
	let x;
	if (b) x = { a: 1 }; else x = {};
	const n: number = x;
	let y;
	if (b) y = 1; else y = "s";
	const m: boolean = y;
}
