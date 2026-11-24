import * as all from './labels';
import { labels } from './labels';
import { labels as renamed } from './labels';
import { Kind } from './two';

type Labels = { [key in import('./one').Kind]: string };
const local: Labels = { ALPHA: 'a', BETA: 'b' } as Labels;

export function show(k: Kind): string {
  return labels[k] + renamed[k] + all.labels[k] + local[k];
}
