export class A {
	m() { return this; }
	n(): this { return this; }
	f = () => this;
	get g() { return this; }
}
export class B extends A {
	k() { return super.m(); }
	j() { return this.n(); }
	h() { const x = this; return [x]; }
}
export const q1: boolean = new B().m;
export const q2: boolean = new B().k;
export const q3: boolean = new B().k();
export const q4: boolean = new B().j;
export const q5: boolean = new A().m;
export const q6: boolean = new B().f;
export const q7: boolean = new B().g;
export const q8: boolean = new B().h();
