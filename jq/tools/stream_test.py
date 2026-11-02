# --stream / --stream-errors on bad input: python3 stream_test.py JQ VJQ (events before the error,
# jq's streaming parser's messages, -n inputs).
import subprocess, sys
J, V = sys.argv[1], sys.argv[2]
cases=['[1,[2,3', '{"a":1,"b":', '[1,2] [3,', '1 2 x', '[1,}', '{"a":[1,{"b":2}]}', '[1,2]\n[3,x]\n[4]\n', '{"a":}', '{,}', '[,]', '{"a" 1}', '{"a":1,}', '[1 2]', '{[1]}', '{"a":1,[2]}', '"abc', '[1,"a\\x"]', '{1:2}', ':', '[1]]', '{"a":1}}', 'nul', '[tru]', '{"a":{"b":[]},"c":{}}', '[[],{}]', '"x" 1 [', '[1,2\n,3]\n[x]\n5\n']
fails=0
for c in cases:
    for args in (['-c','--stream','.'],['-c','--stream-errors','.'],['-c','--stream','-n','[inputs]'],['-c','.']):
        a=subprocess.run([J]+args,input=c.encode(),capture_output=True)
        b=subprocess.run([V]+args,input=c.encode(),capture_output=True)
        if (a.returncode,a.stdout,a.stderr)!=(b.returncode,b.stdout,b.stderr):
            fails+=1
            print('===',repr(c),args); print(' jq: ',a.returncode,a.stdout,a.stderr); print(' vjq:',b.returncode,b.stdout,b.stderr)
print(fails,'fails')
