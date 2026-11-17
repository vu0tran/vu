export {};
declare function r<Mask extends { origin?: true }>(mask: Mask): Mask;
declare function s<Mask extends { origin: true }>(mask: Mask): Mask;
declare function u<Mask extends { origin?: string }>(mask: Mask): Mask;
const x3: number = r({ origin: true as const });
const x4: number = s({ origin: true });
const x5: number = u({ origin: "a" });
const x6: number = r({});
