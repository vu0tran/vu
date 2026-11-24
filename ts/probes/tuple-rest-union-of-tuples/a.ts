import type { Events, Holder, Opts, Server } from './lib';

type Configure = Exclude<Holder['configure'], undefined>;
type First = Parameters<Configure>[0];

export function start(h: Holder, raw: object): void {
  const s = raw as First;
  h.configure?.(s, { depth: 1 });
  s.on('open', (name, opts, done) => {
    void name;
    void opts;
    void done;
  });
}

export const open: Events['open'] = ['x'];
export const open2: Events['open'] = ['x', { depth: 1 }];
export const shut: Events['shut'] = [1, 'a', 'b'];
export const cast = {} as Opts;
export const srv = {} as Server;
