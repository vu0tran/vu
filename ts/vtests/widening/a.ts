export {};
interface SJO { ownerType: string; ownerId: string; ownerMemberId: string | null }
declare function w<T extends SJO>(claimed: { now: Date; jobs: T[] }): T;
const owner = (ownerType: string, ownerId: string, ownerMemberId: string | null = null) => ({ ownerType, ownerId, ownerMemberId });
const r = w({ now: new Date(), jobs: [{ id: 1, ...owner('a', 'b', 'c') }, { id: 2, ...owner('a', 'b') }] });
const b: boolean = r;
