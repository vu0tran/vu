export {};
type K = { origin: string; nodeNames: string[] };
declare function q<Mask extends { [k in keyof K]?: true }>(mask: Mask): Mask;
declare function r<Mask extends { origin?: true }>(mask: Mask): Mask;
declare function s<Mask extends { origin?: boolean }>(mask: Mask): Mask;
const x2: number = q({ origin: true });
const x3: number = r({ origin: true });
const x4: number = s({ origin: true });
