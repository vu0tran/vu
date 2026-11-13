export class A1 {
	m() { return this; }
	n(): this { return this; }
}
export class B1 extends A1 {
	k() { return super.m(); }
	j() { return this.n(); }
}
export const r1: boolean = new B1().m;
export const r2: boolean = new B1().k;
export const r3: boolean = new B1().k();
export const r4: boolean = new B1().j;
export const r5: boolean = new A1().m;
