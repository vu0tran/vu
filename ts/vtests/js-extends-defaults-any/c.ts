// The same in TypeScript: the defaults.
export class Search extends Comp {
  render() {
    const { store } = this.props;
    this.setState({ q: 1 });
  }
}
