import re,time,tempfile,subprocess,urllib.request
from html.parser import HTMLParser
from config import *
CACHE={}
class P(HTMLParser):
 def __init__(self): super().__init__(); self.b=[]; self.skip=0
 def handle_starttag(self,t,a):
  if t in {"script","style","nav","header","footer"}: self.skip+=1
  elif t in {"p","li","div","h1","h2","h3","h4","br","td"} and not self.skip:self.b.append("\n")
 def handle_endtag(self,t):
  if t in {"script","style","nav","header","footer"} and self.skip:self.skip-=1
  elif t in {"p","li","div","h1","h2","h3","h4","td"} and not self.skip:self.b.append("\n")
 def handle_data(self,d):
  if not self.skip:self.b.append(d)
def fetch(url,accept):
 h=CACHE.get(url)
 if h and time.time()-h[0]<TTL:return h[1]
 q=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":accept})
 with urllib.request.urlopen(q,timeout=40) as r:d=r.read(20_000_000)
 CACHE[url]=(time.time(),d);return d
def htmltext():
 p=P();p.feed(fetch(SUMULAS_TRIBUNAL,"text/html").decode("utf-8","replace"))
 return re.sub(r"\n{2,}","\n",re.sub(r"[ \t]+"," ","".join(p.b)))
def pdftext():
 d=fetch(SUMULAS_TU,"application/pdf")
 with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
  f.write(d);f.flush()
  return subprocess.check_output(["pdftotext","-layout",f.name,"-"],timeout=60).decode("utf-8","replace")
STOP={"de","da","do","das","dos","e","a","o","em","para","por","com","um","uma","no","na","nos","nas","lei","art"}
def toks(q):return [x for x in re.findall(r"[a-z0-9áéíóúâêôãõç]+",q.lower()) if len(x)>2 and x not in STOP]
def _rows(text,head,source,label,url,q,limit,invalid_words):
 ms=list(head.finditer(text));qt=toks(q);rows=[];excluded=0
 for i,m in enumerate(ms):
  n=int(m.group(1)); end=ms[i+1].start() if i+1<len(ms) else min(len(text),m.end()+3500)
  body=re.sub(r"\s+"," ",text[m.end():end]).strip()
  marker=(m.group(0)+" "+body[:250]).upper()
  if any(w in marker for w in invalid_words): excluded+=1;continue
  if len(body)<20:continue
  score=sum(t in body.lower() for t in qt)
  if score and (len(qt)<=1 or score>=min(2,len(qt))):
   rows.append((score,{"id":f"{source}:{n}","title":f"{label} {n}","summary":body[:1700],"type":"sumula_tjba","date":"","organization":"Tribunal de Justiça do Estado da Bahia","source":source,"source_label":label,"source_url":url,"official_url":url,"is_official":True,"is_synthetic":False,"retrieved_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"match_score":score}))
 rows.sort(key=lambda z:(-z[0],z[1]["title"]))
 return [r for _,r in rows[:limit]],excluded
def search(q,limit):
 results=[];proof=[]
 try:
  text=htmltext()
  head=re.compile(r"(?im)^\s*S[ÚU]MULA\s+(?:N[ºO.]?\s*)?(\d+)\b")
  r,x=_rows(text,head,"tjba_sumulas_tribunal","TJBA — Súmula",SUMULAS_TRIBUNAL,q,limit,{"CANCELADA","CANCELADO","REVOGADA","REVOGADO"})
  results+=r;proof.append({"source":"tjba_sumulas_tribunal","status":"ok","count":len(r),"invalid_excluded":x,"request_url":SUMULAS_TRIBUNAL,"cache_ttl_seconds":TTL})
 except Exception as e:proof.append({"source":"tjba_sumulas_tribunal","status":"error","error_type":type(e).__name__})
 try:
  text=pdftext()
  head=re.compile(r"(?im)^\s*S[úu]mula\s+n[ºo]\s*(\d+)\s*[-–—:]")
  r,x=_rows(text,head,"tjba_sumulas_tu","TJBA — Turma de Uniformização — Súmula",SUMULAS_TU,q,limit,{"CANCELADA","CANCELADO","REVOGADA","REVOGADO"})
  results+=r;proof.append({"source":"tjba_sumulas_tu","status":"ok","count":len(r),"invalid_excluded":x,"request_url":SUMULAS_TU,"cache_ttl_seconds":TTL})
 except Exception as e:proof.append({"source":"tjba_sumulas_tu","status":"error","error_type":type(e).__name__})
 return results,proof
