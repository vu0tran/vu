type CLS = {
  schoolDistrict: string;
  elementarySchool: string;
  middleSchool: string;
};
type N = Omit<CLS, 'elementarySchool' | 'middleSchool'> & {
  elementarySchool: string[];
  middleSchool: string[];
};
declare const SEL: N;
export function f() {
  for (const [d, selectors] of Object.entries(SEL)) {
    for (const s of selectors) {
      const q: number = s;
    }
  }
}
