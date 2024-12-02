from collections import defaultdict
def solve():
    n, m = map(int, input().split())
    graph = defaultdict(list)
    for _ in range(m):
        x, y = map(int, input().split())
        graph[x].append(y)
        graph[y].append(x)
    visited = [0]*(n+1)
    for i in range(1, n+1):
        if visited[i] == 0:
            queue = [i]
            visited[i] = 1
            while queue:
                node = queue.pop(0)
                for neighbour in graph[node]:
                    if visited[neighbour] == visited[node]:
                        return "NO"
                    if visited[neighbour] == 0:
                        visited[neighbour] = -visited[node]
                        queue.append(neighbour)
    return "YES"

t = int(input())
for _ in range(t):
    print(solve())