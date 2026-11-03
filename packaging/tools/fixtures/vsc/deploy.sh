#!/bin/sh
# a deploy script with the mistakes ShellCheck is known for
dir=$1
cd $dir
for f in `ls *.txt`; do
  echo "copying $f"
  cp $f /tmp/backup
done
if [ $count == 3 ]; then
  echo "three"
fi
read name
echo "hello $name" | grep -q hello && echo yes || echo no
local x=1
[[ -n "$x" ]] && echo "$x"
