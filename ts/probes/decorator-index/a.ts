class A {
  @IsNotEmpty()
  [X]: string
  @a.b
  [Y] = 1
  @c(x[0])
  z = 2
  @(d[0])
  w = 3
}
export {A}
