declare const xs: string[];
export const a = [...xs, 'b'] as [string, string];
export const b: 'z' = a;
