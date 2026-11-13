export type RBM = { mediaType: 'application/json' } | { mediaType: 'multipart/form-data'; uploadLimits?: { a: 1 } };
export type BO = { required?: boolean } & (RBM | { mediaType?: undefined });
declare function strip(o: RBM): RBM;
export function f(options?: BO) {
	const b: boolean = options;
	if (options?.mediaType !== undefined) {
		const c: boolean = options;
		strip(options);
	}
}
