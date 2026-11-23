type To = string | { pathname: string };
type Opts = { replace?: boolean };
type P = [to: To, options?: Opts] | [delta: number];
export function nav(...props: P) {
  const [deltaOrTo, options] = props;
  const a: number = deltaOrTo;
  const b: number = options;
  if (typeof deltaOrTo === 'number') return deltaOrTo;
  return options?.replace;
}
declare const q: [1, 2] | [3];
const [, second] = q;
const c2: string = second;
