type Interp = string | number | boolean | null | undefined | { [k: string]: Interp } | Interp[];
declare const css: {
  (template: TemplateStringsArray, ...args: Interp[]): string;
  (...args: Interp[]): string;
};
const a = css`
  opacity: 0.5;
`;
const n = 3;
const b = css`
  width: ${n}px;
`;
const c1: number = a;
const d: number = b;
export { c1, d };
