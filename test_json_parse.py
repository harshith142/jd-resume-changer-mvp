import json

# Test 1: LLM outputs literal \n in JSON (escaped backslash-n)
# In JSON this would be: {"latex": "\\documentclass{article}\\n\\begin{document}"}
# Which means the JSON contains: backslash, backslash, n
# When parsed, Python gets: backslash, n (literal)
s1 = r'{"latex": "\\documentclass{article}\n\begin{document}"}'
print('Test 1 - JSON with escaped backslash-n:')
print('  Input:', s1)
try:
    parsed1 = json.loads(s1)
    print('  Parsed:', repr(parsed1['latex']))
except Exception as e:
    print('  Error:', e)

# Test 2: LLM outputs actual newlines in JSON string
# JSON doesn't allow raw newlines, so this would be invalid
# But if they use \n in JSON (meaning newline), it becomes actual newline
# In JSON: {"latex": "\documentclass{article}\n\begin{document}"}
# Note: single backslash in JSON = escape sequence
s2 = '{"latex": "\\documentclass{article}\\n\\begin{document}"}'
print('Test 2 - JSON with newline escape:')
print('  Input:', s2)
try:
    parsed2 = json.loads(s2)
    print('  Parsed:', repr(parsed2['latex']))
except Exception as e:
    print('  Error:', e)

# Test 3: What if LLM outputs raw newlines (invalid JSON but some parsers allow)
s3 = '{\n  "latex": "\\documentclass{article}\n\\begin{document}"\n}'
print('Test 3 - Multi-line JSON with raw newlines:')
print('  Input:', repr(s3))
try:
    parsed3 = json.loads(s3)
    print('  Parsed:', repr(parsed3['latex']))
except Exception as e:
    print('  Error:', e)