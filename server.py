import json,time,uuid,urllib.request,urllib.parse
from collections import defaultdict,deque
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from config import *
from scrape import search
def now():return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
def call(url,method="GET",payload=None):
 d=None if payload is None else json.dumps(payload,ensure_ascii=False).encode()
 h={"User-Agent":UA,"Accept":"application/json"}
 if d:h["Content-Type"]="application/json"
 with urllib.request.urlopen(urllib.request.Request(url,data=d,headers=h,method=method),timeout=90) as r:return json.load(r)
def interleave(items,limit):
 g=defaultdict(deque);order=[]
 for x in items:
  s=x.get("source","unknown")
  if s not in g:order.append(s)
  g[s].append(x)
 out=[]
 while len(out)<limit and any(g[s] for s in order):
  for s in order:
   if g[s] and len(out)<limit:out.append(g[s].popleft())
 return out
SOURCES=[
 {"id":"tjba_sumulas_tribunal","name":"TJBA — Súmulas do Tribunal","status":"online","coverage":["sumulas","jurisprudencia_predominante"],"official":True,"requires_secret":False,"url":SUMULAS_TRIBUNAL},
 {"id":"tjba_sumulas_tu","name":"TJBA — Súmulas da Turma de Uniformização","status":"online","coverage":["sumulas","juizados_especiais"],"official":True,"requires_secret":False,"url":SUMULAS_TU},
 {"id":"tjba_portal_jurisprudencia","name":"TJBA — Consulta de Jurisprudência","status":"manual_official_portal","coverage":["acordaos","decisoes","ementas"],"official":True,"requires_secret":False,"url":PORTAL}
]
ONLINE=["camara_proposicoes","senado_processos","senado_legislacao","tse_ckan","tjsc_sumulas","tjsc_enunciados","tjrs_sumulas_tr_fazenda","tjpr_enunciados_turmas","tjpr_enunciados_tuj","tjsp_comesp_enunciados","tjsp_pesquisas_tematicas","tjmg_sumulas_civeis","tjmg_sumulas_criminais","tjmg_sumulas_grupo_criminal","tjrj_sumulas","tjba_sumulas_tribunal","tjba_sumulas_tu"]
def run(path,p):
 st=time.monotonic();q=str(p.get("query") or p.get("q") or "").strip();limit=max(1,min(int(p.get("limit",10)),20))
 up="/v1/search" if path=="/v1/search" else path;b=call(UPSTREAM+up,"POST",p)
 results=list(b.get("results") or []);e=list(b.get("evidence") or []);w=list(b.get("warnings") or [])
 try:
  f,pr=search(q,limit);results+=f;e+=pr
 except Exception as x:w.append(f"tjba_curated unavailable: {type(x).__name__}; nenhum resultado foi inventado.")
 seen=set();d=[]
 for x in results:
  k=(x.get("source"),x.get("id"),x.get("title"))
  if k not in seen:seen.add(k);d.append(x)
 final=interleave(d,limit)
 return {"status":"ok","service":"lex-search-aggregator","version":VERSION,"generated_at":now(),"trace_id":str(uuid.uuid4()),"query":q,"scope":b.get("scope","all"),"result_count":len(final),"results":final,"evidence":e,"sources_used":sorted({x.get("source") for x in final if x.get("source")}),"integrity":{"official":sum(bool(x.get("is_official")) for x in final),"synthetic":sum(bool(x.get("is_synthetic")) for x in final),"source_urls_present":sum(bool(x.get("source_url")) for x in final)},"warnings":w,"human_review_required":True,"no_invention_policy":True,"duration_ms":int((time.monotonic()-st)*1000)}
class H(BaseHTTPRequestHandler):
 def out(s,c,o):
  d=json.dumps(o,ensure_ascii=False).encode();s.send_response(c);s.send_header("Content-Type","application/json; charset=utf-8");s.send_header("Content-Length",str(len(d)));s.send_header("Cache-Control","no-store");s.end_headers();s.wfile.write(d)
 def body(s):
  n=int(s.headers.get("Content-Length","0") or 0)
  if n>64000:raise ValueError("payload_too_large")
  return json.loads((s.rfile.read(n) if n else b"{}").decode())
 def do_GET(s):
  p=urllib.parse.urlparse(s.path).path
  if p in {"/health","/v1/health"}:return s.out(200,{"status":"ok","service":"lex-search-aggregator","version":VERSION,"generated_at":now(),"real_sources_online":ONLINE,"human_review_required":True,"no_invention_policy":True})
  if p in {"/ready","/v1/readiness"}:return s.out(200,{"status":"ready","version":VERSION,"online_sources":ONLINE,"generated_at":now()})
  if p in {"/v1/sources","/v1/sources/registry"}:
   b=call(UPSTREAM+"/v1/sources");return s.out(200,{"status":"ok","service":"lex-search-aggregator","version":VERSION,"generated_at":now(),"sources":list(b.get("sources") or [])+SOURCES,"human_review_required":True,"no_invention_policy":True})
  s.out(404,{"error":"not_found"})
 def do_POST(s):
  p=urllib.parse.urlparse(s.path).path
  if p not in {"/v1/search","/v1/search/global","/v1/search/legislacao","/v1/search/datasets"}:return s.out(404,{"error":"not_found"})
  try:
   x=s.body()
   if not str(x.get("query") or x.get("q") or "").strip():return s.out(422,{"error":"query_required"})
   s.out(200,run(p,x))
  except Exception as e:s.out(500,{"error":"tjba_curated_connector_error","detail":type(e).__name__})
 def log_message(s,*a):pass
ThreadingHTTPServer(("0.0.0.0",PORT),H).serve_forever()
