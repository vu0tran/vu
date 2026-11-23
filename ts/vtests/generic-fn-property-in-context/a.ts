// A generic function as an object literal's property value inside a generic call's inference ({ useTheme }): instantiated in the property's contextual signature, its type parameter's default where nothing infers it.
interface MuiTheme { palette: string }
declare function useTheme<T = MuiTheme>(): T;
declare function useT2<T>(): T;
declare function mk<Theme>(p: { useTheme: () => Theme }): Theme;
const a: number = mk({ useTheme });
const b: number = mk({ useTheme: useT2 });
declare function mk2<Theme>(u: () => Theme): Theme;
const c: number = mk2(useTheme);
