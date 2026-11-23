// A JavaScript class extending a generic class without type arguments: they are any (defaults
// of {} or unknown).
export class Search extends Comp {
  render() {
    const { store } = this.props;
    const n = store.rules;
    this.setState({ q: 1 });
    /** @type {number} */
    const s = this.state;
    return n;
  }
}
