export type El<T> = { e: NonNullable<T>[number & keyof NonNullable<T>]; s: NonNullable<T>[string & keyof NonNullable<T>] };
export type El2<T, K extends number> = { e: NonNullable<T>[K] };
