export const ef1 = (arr: number[]) => {
	const xs = [];
	for (let i = 0; i < arr.length; i++) { xs.push(arr[i]); }
	return xs;
};
export const ef2 = (arr: number[]) => {
	const xs = [];
	for (let i = 0; i < arr.length; i++) { if (arr[i] > 1) xs.push(arr[i]); else xs.push("s"); }
	return xs;
};
export const ef3 = (arr: number[]) => {
	const xs = [];
	for (let i = 0; i < arr.length; i++) { if (arr[i] > 1) xs.push(arr[i]); else if (i) { return arr; } else xs.push("s"); }
	return xs;
};
const b1: boolean = ef1([]); const b2: boolean = ef2([]); const b3: boolean = ef3([]);
