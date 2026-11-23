import { Photo } from './missing';
declare const photos: Photo[];
declare const anys: any[];
declare function f(): boolean;
export const r1 = photos.map((photo) => {
  if (f()) return photo;
  return { a: 1 };
});
export const r2 = photos.map((photo) => photo);
export const r3 = anys.map((p) => {
  if (f()) return p;
  return { a: 1 };
});
export const r4 = photos.map((photo) => {
  return photo;
});
