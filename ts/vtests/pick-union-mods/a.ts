interface Ext { [extensionName: `x-${string}`]: any }
interface S30 extends Ext { type?: string; description?: string; example?: any; nullable?: boolean }
interface S31 extends Ext { type?: string | string[]; description?: string; example?: any; examples?: any[] }
type SO = S30 | S31;
type M = Omit<SO, 'example' | 'examples'> & { example?: any };
export const e1: Omit<SO, 'example'> = { description: 'x' };
export const e2: M = { description: 'x' };
export const e3: Omit<S30, 'example'> = { description: 'x' };
type K = keyof SO;
export const k: K = "description";
interface S2 { a?: string }
export const e4: Omit<S2 | S30, 'example'> = { description: 'x' };
interface R1 { readonly id: string; n?: number } interface R2 { id: string; n: number }
export const e5: Pick<R1 | R2, 'id' | 'n'> = { id: 'a' };
declare const e6: Pick<R1 | R2, 'id'>;
e6.id = 'b';
