// noErrorTruncation: types in messages printed in full (no { ...; }, no ... N more ..., no cut at 317)
declare const r: Record<"bathroom" | "exterior" | "interior" | "kitchen", {
  status: "completed" | "failed" | "pending" | "picking" | "planning" | "rendering" | "skipped";
  error?: string;
  sourceImages?: { url: string; rationale?: string; width: number; height: number };
  itemPhoto?: { url: string; itemAddressLabel: string; roomType?: string; conditionScore?: number };
  comp?: { addressLabel: string; streetAddress: string; fullAddress: string; closePrice?: number };
  plan?: { today: string[]; light: { description: string }[]; targeted: { description: string }[] };
  alpha: number; beta: number; gamma: number; delta: number; epsilon: number; zeta: number;
  promptVersion: string;
}>;
const n1: number = r;
const n2: number = r.kitchen;
declare const u: ["a1" | "a2" | "a3" | "a4" | "a5" | "a6" | "a7" | "a8" | "a9" | "b1" | "b2" | "b3" | "b4" | "b5" | "b6" | "b7" | "b8" | "b9" | "c1" | "c2" | "c3" | "c4" | "c5" | "c6" | "c7" | "c8" | "c9" | "d1" | "d2" | "d3" | "d4" | "d5" | "d6" | "d7" | "d8" | "d9" | "e1" | "e2" | "e3", ...("x1" | "x2" | "x3" | "x4" | "x5" | "x6" | "x7" | "x8" | "x9" | "y1" | "y2" | "y3" | "y4" | "y5" | "y6" | "y7" | "y8" | "y9")[]];
const n3: number = u;
