export {};
declare const o: { a_x: number; b_x: string; a_y: boolean };
declare const k: 'a' | 'b';
const v1: boolean = o[`${k}_x`];
const v2: boolean = o[(`${k}_x`)];
const kk = `${k}_x`;
const v3 = o[kk];
