export class LSc {
	n?: number;
	m?: string;
	hasN(): this is { n: number } { return this.n !== undefined; }
	hasM(): this is { m: string } { return this.m !== undefined; }
	b() {
		if (this.hasN()) { const w: string = this.n; if (this.hasM()) { const u: number = this.m; const w2: string = this.n; } }
		if (this.hasN() && this.hasM()) { const w3: string = this.n; }
	}
}
