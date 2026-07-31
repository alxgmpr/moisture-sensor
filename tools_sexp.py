import re
def parse(text):
    tok = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')
    stack=[[]]
    for t in tok.findall(text):
        if t=='(': stack.append([])
        elif t==')':
            v=stack.pop(); stack[-1].append(v)
        elif t.startswith('"'): stack[-1].append(t[1:-1].encode().decode('unicode_escape'))
        else: stack[-1].append(t)
    return stack[0][0]
def find(node,key):
    return [c for c in node if isinstance(c,list) and c and c[0]==key]
def first(node,key):
    r=find(node,key); return r[0] if r else None
