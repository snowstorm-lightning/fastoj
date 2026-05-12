import ast
import sys

lines = sys.stdin.read().strip().split("\n")
nums = ast.literal_eval(lines[0])
target = int(lines[1])

hashmap = {}
for i, num in enumerate(nums):
    complement = target - num
    if complement in hashmap:
        print([hashmap[complement], i])
        break
    hashmap[num] = i
