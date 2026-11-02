r=$1; n=$(echo $r | tr / _)
for f in .golangci.yml .golangci.yaml .golangci.toml .golangci.json; do
  code=$(curl -sS -o cfg/$n$f -w '%{http_code}' "https://raw.githubusercontent.com/$r/HEAD/$f")
  if [ "$code" = 200 ]; then echo "$r $f"; exit 0; fi
  rm -f cfg/$n$f
done
