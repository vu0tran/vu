export const a: Array<[p: string, v: string, x: unknown]> = ['a'].flatMap((p) => [
  [p, 'primitive', 'value'],
  [p, 'object', { name: 'value' }],
  [p, 'array', [1, 'value']],
]);
