type MR = { ok: true; v: number } | { ok: false; e: unknown };
type Link = { sd: string | null; pi: number };
type St = { key: string; sd: string; pi: number };
type Frame = { parentResults: MR[] } & ({ link: Link } | (St & { results: MR[] }));
declare function norm(a: number, b: string | null): [number, string | null];
declare function step(): { item: number } | { next: Link[] };
declare function ok(v: number): MR;
declare function bad(e: unknown): MR;
export function f(init: Link) {
  const results: MR[] = [];
  const stack: Frame[] = [{ link: init, parentResults: results }];
  for (let frame = stack.pop(); frame !== undefined; frame = stack.pop()) {
    let state: St | undefined;
    let result: MR;
    try {
      if ('link' in frame) {
        const { link } = frame;
        const [pi, sd] = norm(link.pi, link.sd);
        if (!sd) throw new Error('x');
        state = { key: 'k', sd, pi };
        const s = step();
        if ('next' in s) {
          const childResults: MR[] = [];
          stack.push({ ...state, results: childResults, parentResults: frame.parentResults });
          for (let i = s.next.length - 1; i >= 0; i--) stack.push({ link: s.next[i], parentResults: childResults });
          continue;
        }
        result = ok(s.item);
      } else {
        state = frame;
        result = ok(frame.pi + frame.results.length);
      }
    } catch (error) {
      result = bad(error);
    }
    if (state) { state.key; }
    frame.parentResults.push(result);
  }
  return results;
}
