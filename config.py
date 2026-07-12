import os
PORT=int(os.getenv("PORT","8080"))
UPSTREAM=os.getenv("LEX_UPSTREAM","http://homosapiens-lex-tjrj-curated-v15:8080")
VERSION="0.16.0-tjba-curated"
UA="Lex-HomoSapiens/0.16"
TTL=1800
SUMULAS_TRIBUNAL="https://www.tjba.jus.br/portal/sumulas/"
SUMULAS_TU="https://www.tjba.jus.br/juizadosespeciais/wp-content/uploads/2026/06/SUMULAS_ATUALIZADAS_TU-1.pdf"
PORTAL="https://jurisprudencia.tjba.jus.br/"
