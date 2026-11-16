import sys; sys.path.insert(0,'.')
import tom_sim
from tom_sim import PROFILES
PROFILES['lawyers']=dict(removal=.10,wipe=.07,ench=.08,creature_rate=.5,disrupt=.40)   # counters, Verdict/Time Wipe/Austere, Cyclonic Rift
PROFILES['lawyers_hard']=dict(removal=.12,wipe=.09,ench=.10,creature_rate=.45,disrupt=.55)
from tom_tools import load,swap,play
import lawyer
b=load('tom_deck.json')
CA='The Creation of Avacyn'; BS='The Bath Song'; SK='Showdown of the Skalds'; EO='Esper Origins'
tom=swap(b,[('Three Blind Mice',CA),('Terra, Magical Adept',EO),('Selesnya Signet',BS),('Simic Signet',SK)])
N=int(sys.argv[1])
L={p:lawyer.play(p,N) for p in ('bracket3','bracket4')}
def race(a,b):
    ta=wa=0;tb=0;none=0
    for x,y in zip(a,b):
        if x==99 and y==99: none+=1
        elif x<y: ta+=1
        elif y<x: tb+=1
        else: ta+=.5; tb+=.5
    n=len(a); return ta/n,tb/n,none/n
for prof in ('bracket3','bracket4','lawyers','lawyers_hard'):
    t=[w for w,h in play(tom,prof,N)]
    s=lambda arr,k:sum(x<=k for x in arr)/len(arr)
    print(prof,'TOM by8/12/16',[round(s(t,k),3) for k in (8,12,16)])
    for lp in ('bracket3','bracket4'):
        # independent samples: pair Tom game i with Lawyer game (i*7 mod N) to avoid same-seed coupling
        la=[L[lp][(i*7+3)%N] for i in range(N)]
        a,bb,n=race(t,la)
        print(f'   vs Lawyers({lp}) by8/12/16',[round(s(la,k),3) for k in (8,12,16)],f'| Tom first {a:.1%}  Lawyers first {bb:.1%}  neither by T16 {n:.1%}')
print('done')
