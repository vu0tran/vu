import { decode, VERSION, Enc, type Options } from 'ic';
export const s: number = decode('a', 'b');
export const v: string = VERSION;
export const o: Options = { strip: 1 };
export const e = new Enc().x;
