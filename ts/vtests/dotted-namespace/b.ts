// namespace a.b.c written dotted: each level a namespace, the body the innermost's; names inside
// resolve through every level and the other blocks
declare const t: Tags;
export const a: number = t['gmp-map'];
declare const t2: Tags2;
export const b: string = t2.a;
export const m = new google.maps.Map();
export const x: string = m.x;
export const v: google.maps.places.Inner = 1;
