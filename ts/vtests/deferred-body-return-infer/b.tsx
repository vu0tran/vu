// a deferred body keeps the narrowings where it is (code !== null && ...: code there)
declare function useState<T>(v: T): [T, (f: (p: T) => T) => void];
declare function Dlg(p: { onCancel: (n: string) => void }): null;
export function Comp() {
  const [code] = useState<'a' | 'b' | null>(null);
  const [, setNotes] = useState<Record<string, string>>({});
  return code !== null && Dlg({ onCancel: (draft) => { setNotes((prev) => ({ ...prev, [code]: draft })); const k: 'a' | 'b' = code; void k; } });
}
