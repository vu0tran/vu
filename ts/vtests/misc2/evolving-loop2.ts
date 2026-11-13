const oi2 = Symbol('o');
export const ens2 = (arr: number[]) => {
	const newArr = [];
	for (let i = 0; i < arr.length; i++) {
		newArr.push({ [oi2]: i });
	}
	return newArr;
};
const b: boolean = ens2([]);
