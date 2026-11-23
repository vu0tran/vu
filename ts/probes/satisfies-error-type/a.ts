import type { Missing } from './missing';

declare function use(x: unknown): void;

export function f(flag: boolean) {
  const input = {
    a: 'x',
    flag,
  } satisfies Missing;
  use({ input });
  const other = { a: 1 } as Missing;
  use(other);
  const third: Missing = { a: 1 };
  use(third);
  return input;
}
