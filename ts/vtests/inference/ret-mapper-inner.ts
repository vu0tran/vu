export {};
declare function reg(o: { find: () => Promise<Set<string>> }): void;
reg({ find: async () => await Promise.resolve(new Set()) });
reg({ find: async () => Promise.resolve(new Set()) });
reg({ find: async () => new Set() });
reg({ find: async () => { return await Promise.resolve(new Set()); } });
const f: () => Promise<Set<number>> = async () => await Promise.resolve(new Set());
