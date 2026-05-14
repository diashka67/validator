


f = open('text.txt', mode ='r')

d = {}
for s in f.read().split():
    d[s] = d.get(s, 0) + 1

print(d, sep = '\n')

def my_get(d: dict, k, default=None):
    try:
        return dict[k]
    except KeyError as e:
        print(e)
        return default