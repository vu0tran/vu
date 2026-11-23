import { C, IA, IB, ns } from './m';
declare const e: unknown;
const a1: number = e as C;
const a2: number = e as IA;
const a3: number = e as IB;
const a4: number = e as ns.IN;
const a5: number = e as IA<number>;
const a6: number = e as IB<number>;
const a7: number = e as IA<unknown, any>;
// An alias whose body is another generic alias reaching a class reference (IB = I0<T, D> = C<T, D>)
// keeps its name (tsgo); named through an import, its alias arguments are the written ones.
