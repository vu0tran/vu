// null and undefined comparisons on a type parameter: T & ({} | null), NonNullable<T>, ??, instanceof
export {};
type O<T> = { acceptJSObject?: boolean; fallbackValue?: T; errorMessage?: string };
declare function p(s: string): unknown;
export const jsonParse = <T,>(s: string, options?: O<T>): T => {
	try {
		return JSON.parse(s) as T;
	} catch (error) {
		if (options?.acceptJSObject) {
			try {
				return p(s) as T;
			} catch (e) {
			}
		}
		if (options?.fallbackValue !== undefined) {
			if (options.fallbackValue instanceof Function) {
				return options.fallbackValue();
			}
			return options.fallbackValue;
		}
		throw error;
	}
};
