// (an optional chain's root narrowed by truthiness, through an aliased condition: a generic mapped
// type member, Partial<Record<T, X>>, is an object and stays)
export function f<T extends string>(keys: readonly T[], disabled?: Partial<Record<T, string>>) {
  return keys.map((key) => {
    const reason = disabled?.[key];
    const isDisabled = !!reason;
    const shown: number = isDisabled ? disabled : 0;
    return shown;
  });
}
