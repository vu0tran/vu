export {};
declare const q: { readonly w: 1 } & { w: number };
q.w = 1;
declare const r: { readonly w: 1 } & { readonly w: number };
r.w = 1;
