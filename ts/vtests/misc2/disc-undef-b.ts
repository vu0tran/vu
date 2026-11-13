export type RBM = { mediaType: 'application/json' } | { mediaType: 'multipart/form-data'; uploadLimits?: { a: 1 } };
export type BO = { required?: boolean } & (RBM | { mediaType?: undefined });
export type BO2 = { required?: boolean } & ({ mediaType: 'a' } | { mediaType: 'b' } | { mediaType?: undefined });
export function f(o: BO, o2: BO2, o3?: BO2) {
	if (o.mediaType !== undefined) { const c: boolean = o; }
	if (o2.mediaType !== undefined) { const c: boolean = o2; }
	if (o3?.mediaType !== undefined) { const c: boolean = o3; }
}
