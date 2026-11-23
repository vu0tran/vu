export function Disclosure(props: { rate: { asOf: string } }) {
  const asOf = props.rate.asOf;
  return (
    <p>
      Terms and conditions apply. Actual loan terms will vary, among other things.
      {asOf ? `Rate as of ${asOf}. ` : null}
      See <a href="/terms">the terms</a>.
    </p>
  );
}
