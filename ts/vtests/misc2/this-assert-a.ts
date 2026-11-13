export interface LP { isL(f: string): boolean }
export class LS {
	lp: LP | null = null;
	private ap(): asserts this is { lp: LP } { if (!this.lp) throw new Error(); }
	private isp(): this is { lp: LP } { return !!this.lp; }
	a(f: string) {
		this.ap();
		const b: boolean = this.lp.isL(f);
		const x: string = this.lp;
		return b;
	}
	b() {
		if (this.isp()) { const y: string = this.lp; }
		const z: string = this.lp;
	}
}
declare const o: LS;
o.ap;
