namespace N { export class Base { x = 1; } export namespace Deep { export class B2<T> { y!: T; } } }
export class A extends N.Base { z = this.x; }
export class C extends N.Deep.B2<string> { w: number = this.y; }
export const a: string = new A().z;
