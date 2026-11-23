// An assertion as an assignment target, (x as T) = v: the value is checked against the asserted type
// (a package's DueFeesEdit).
interface Fee { name: string; at: Date | null; cents: number }
export function set(fee: Fee, key: keyof Fee, value: string | Date | null) {
  if (key === 'cents') fee[key] = Number(value);
  else (fee[key] as string | Date | null | undefined) = value;
  let x: unknown = 1;
  (x as number) = 'a';
  const n: number = x;
}
