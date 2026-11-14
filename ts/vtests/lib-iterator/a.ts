const seg = new Intl.Segmenter("en", { granularity: "grapheme" });
for (const { segment, index } of seg.segment("abc")) { const n: number = segment; const s: string = index; }
const all = [...seg.segment("x")];
const a2: string = all;
export {};
