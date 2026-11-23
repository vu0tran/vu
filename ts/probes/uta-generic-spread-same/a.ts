export function seg<R extends { path: string }>(route: R): R {
  return { ...route, path: route.path.replace('a', 'b') } as R;
}
export function seg2<R extends { path: string }>(route: R): R {
  const x = { ...route, path: 'b' } as R;
  return x;
}
export function seg3<R extends { path: string }>(route: R) {
  return { ...route, extra: 1 } as R;
}
export function seg4<R extends { path: string }>(route: R): R {
  return { ...route } as R;
}
