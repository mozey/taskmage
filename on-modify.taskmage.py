#!/Users/mozey/.venvs/taskmage-python3.4.3/bin/python
import sys, json

print("--> taskmage")

f = open("/Users/mozey/pro/taskmage/log", mode="a")
f.write("\n")
f.write("---------------------------------------------------- taskmage\n")
f.write(json.dumps(sys.argv))
f.write("\n")
data = sys.stdin.readlines()
f.write(json.dumps(data))


print("taskmage --->")
sys.exit(0)

