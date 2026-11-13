// arguments in a function (through arrows): IArguments
export {};
function f(a: number) {
	const n: string = arguments.length;
	const g = () => { const m: string = arguments; return arguments[0]; };
	const q: string = g();
	const x: number = arguments[0];
}
class K { m() { const z: string = arguments.length; } }
