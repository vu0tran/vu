interface Rec { id: string }
export function mk(rec: Rec | undefined) {
  let record = rec;
  return {
    get record() {
      return record;
    },
    set record(value) {
      const z: number = value;
      record = value;
    },
  };
}
