type Seg<T> = Omit<T, 'search'> & { search?: string };
declare const a: Seg<{ [k: string]: unknown }>;
const n1: number = { ...a };
declare const c: { [k: string]: unknown } & { search?: string };
const n3: number = { ...c };
declare const d: { [k: string]: string | undefined } & { search?: string };
const n4: number = { ...d };
declare const e: Omit<{ x: 1 }, 'y'> & { search?: string };
const n5: number = { ...e };

declare const g: { [k: string]: number } & { [k: string]: 1 | 2 } & { a: 1 };
const n6: number = { ...g };
declare const h: { [k: number]: string } & { x: string };
const n7: number = { ...h, y: 1 };
