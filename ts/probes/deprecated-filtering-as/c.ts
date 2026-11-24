import { use } from './b';

export function go(id: string): void {
  const { track } = use();
  track('sales', 'viewed', {
    leadKey: id,
    leadUuid: id,
  });
  track('sales', 'signed', { leadKey: '', offer: id });
  use().track('sales', 'viewed', { leadKey: id });
}
