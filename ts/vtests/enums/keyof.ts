declare const o: { Red: 1, Green: 2, Blue: 3 };
export const k: keyof typeof o = "Pink";
export enum E2 { Zed, Alpha }
export const k3: keyof typeof E2 = "x";
