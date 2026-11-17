export {};
declare function r<Mask extends { origin?: true }>(mask: Mask): Mask;
declare function r2<Mask extends { origin?: true | undefined }>(mask: Mask): Mask;
declare function r3<Mask extends { origin: true | undefined }>(mask: Mask): Mask;
declare function r4<Mask extends { origin?: true; b?: 1 }>(mask: Mask): Mask;
const x3: number = r({ origin: true });
const x4: number = r2({ origin: true });
const x5: number = r3({ origin: true });
const x6: number = r4({ b: 1 });
