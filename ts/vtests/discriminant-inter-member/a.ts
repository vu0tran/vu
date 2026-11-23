const Kinds = ['TEXT', 'SELECTED_OPTIONS', 'PHOTOS', 'VIDEOS', 'AUDIOS'] as const;
type Kind = (typeof Kinds)[number];
type Base = { kind: Kind };
type T1 = Base & { kind: 'TEXT'; text: string };
type T2 = Base & { kind: 'SELECTED_OPTIONS'; values: string[] };
type T3 = Base & { assetIds: string[]; kind: 'PHOTOS' | 'VIDEOS' | 'AUDIOS' };
type R = T1 | T2 | T3;
type P = { response: R | null };
export function f(prompt: P | undefined): string {
  const response = prompt?.response;
  if (response?.kind !== 'SELECTED_OPTIONS') {
    return '';
  }
  const n: number = response;
  return response.values[0] ?? '';
}
export function g(prompt: P): string[] {
  return prompt.response?.kind === 'PHOTOS' ? prompt.response.assetIds : [];
}
