# --seq input differential test: python3 seq_test.py JQ VJQ (RS-separated records, truncation,
# resync, jq's line-reading quirks; with -s, -n inputs, try input).
import subprocess, sys, sys
J, V = sys.argv[1], sys.argv[2]
RS='\x1e'
cases=[RS+'1'+RS+'[2]', RS+'1\n'+RS+'2 ', RS+'[1,2'+RS+'3 ', RS+'{"a":1}'+RS+'"x"', '1 2 3', RS+'tru'+RS+'true ', RS+'[1,}'+RS+'4 ', RS+'[1,}', RS+'1 2'+RS, RS+'"abc'+RS+'5\n', '\n\n'+RS+'[1,\n2'+RS+'{"a":\n'+RS+'7 ', RS+'nul', RS+'null', RS+'12', RS+'12\n', RS*3+'1 ', '[1]'+RS+'2 ', RS+'{"a":1}x'+RS+'8 ', RS+'"a"'+RS, RS+'1.5e'+RS+'9 ', '',
  RS+'1\n'+RS+'2\n', RS+'[1]\n'+RS+'[2]\n'+RS+'[3]\n', RS+'{"a":[1,2]}\n'+RS+'{"b":\n'+RS+'3\n', RS+'"x"\n'+RS+'"y"\n', RS+'1 '+RS+'\n2\n', RS+'[1]'+RS+'[2]'+RS+'[3]\n', '[1,', '1 [1,', '{"a":1} x']
fails=0
for c in cases:
    for args in (['-c','.'],['-c','--seq','.'],['-c','--seq','-s','.'],['-n','-c','[inputs]'],['-n','-c','try input catch .'],['-c','--seq','-n','[inputs]']):
        a=subprocess.run([J]+args,input=c.encode(),capture_output=True)
        b=subprocess.run([V]+args,input=c.encode(),capture_output=True)
        if (a.returncode,a.stdout,a.stderr)!=(b.returncode,b.stdout,b.stderr):
            fails+=1
            print('===',repr(c),args); print(' jq: ',a.returncode,a.stdout,a.stderr); print(' vjq:',b.returncode,b.stdout,b.stderr)
print(fails, "fails")
