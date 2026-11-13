export interface LPb { isL(f: string): boolean }
export class LSb {
	lp: LPb | null = null;
	n?: number;
	isp(): this is { lp: LPb } { return !!this.lp; }
	hasN(): this is { n: number } { return this.n !== undefined; }
	b() {
		if (!this.isp()) { const y: string = this.lp; return; }
		const z: string = this.lp;
		if (this.hasN() && this.isp()) { const w: string = this.n; }
	}
}
function g(o: LSb) {
	if (o.isp()) { const v: string = o.lp; }
	const v2: string = o.lp;
}
