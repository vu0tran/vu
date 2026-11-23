/**
 * @param enumType the enum, e.g. MyEnum
 * @param exampleValue a value of it
 */
export function enumValues<ENUM_TYPE, ENUM_INSTANCE>(enumType: ENUM_TYPE, exampleValue: ENUM_INSTANCE): ENUM_INSTANCE[] {
  let out: ENUM_INSTANCE[] = [];
  for (const key in enumType) {
    const numeric = !isNaN(Number(key));
    if (numeric) {
      continue;
    }
    const v = enumType[key] as unknown as ENUM_INSTANCE;
    out.push(v);
  }
  out.push(exampleValue);
  return out;
}
