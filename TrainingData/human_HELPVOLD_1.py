n=int(input())
l=list(map(int,input().split()))[:n]
le=len(l)
l.sort()
a=0
b=1 
m=[]
while(1):
    m.append(l[a]*l[b])
    a+=1 
    b+=1 
    if(b==le):
        break
print(sum(m))
