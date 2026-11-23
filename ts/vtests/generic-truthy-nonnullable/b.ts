export {};
interface W { describe(): number; upload(f: string): void; frames(): string[] }
type B = Pick<W, 'describe'> & Partial<Pick<W, 'upload' | 'frames'>>;
declare const options2: { browser: B };
function capability2<K extends keyof B>(name: K) {
  const method = options2.browser[name];
  if (!method) throw new Error(`no ${name}`);
  return method;
}
const g2: number = capability2('upload');
