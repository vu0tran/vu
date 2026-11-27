import { View } from './view';
function Pair() {
  function first() {
    return second();
  }
  function second() {
    return 1;
  }
  return <View a={first} b={second} />;
}
export default Pair;
