type C = { enabled: false } | { enabled: true; provider: 'x'; include: string[] };
declare function cf(): C | undefined;
declare function cg(): C;
declare function ch(): { enabled: boolean } | {};
export const a = { enabled: true, provider: 'v8', ...cf() };
export const b = { enabled: true, provider: 'v8', ...cg() };
export const d = { enabled: true, ...ch() };
