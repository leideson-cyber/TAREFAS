import time
import requests
import pandas as pd
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Painel de Tarefas - Grupo Mirantes")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQY-3uqG_5o88u0JCHNz9WjUcsYorKGVrN9C1-lFM8Z2rGgH_OvJrPqwJOeeOL3FwsZEpGSlP1p00sS/pub?gid=0&single=true&output=csv"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyUoTxlohCl6OKvKybpGpOZ14tGHS18H4HcBWP7XvUyVa90xtKEQJCbJJRXpdkoqJno/exec"

CACHE_TAREFAS = []
ULTIMA_ATUALIZACAO = 0
TEMPO_CACHE_SEGUNDOS = 15

def carregar_dados_do_csv():
    global CACHE_TAREFAS, ULTIMA_ATUALIZACAO
    try:
        df = pd.read_csv(CSV_URL, dtype=str).fillna("")
        tasks = []
        for _, row in df.iterrows():
            if str(row.get("ID", "")).strip():
                tasks.append({
                    "id": str(row.get("ID", "")).strip(),
                    "company": str(row.get("Empresa", "")).strip(),
                    "title": str(row.get("Atividade", "")).strip(),
                    "assignee": str(row.get("Responsável", "")).strip(),
                    "date": str(row.get("Prazo", "")).strip(),
                    "initialDate": str(row.get("PrazoInicial", row.get("Prazo", ""))).strip(),
                    "status": str(row.get("Status", "A FAZER")).strip(),
                    "createdAt": str(row.get("CriadoEm", "")).strip(),
                    "completedAt": str(row.get("ConcluidoEm", "")).strip(),
                    "obs": str(row.get("Observacoes", "")).strip()
                })
        CACHE_TAREFAS = tasks
        ULTIMA_ATUALIZACAO = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] Cache atualizado: {len(tasks)} tarefas.")
    except Exception as e:
        print("Erro ao atualizar o cache:", e)

@app.on_event("startup")
def startup_event():
    carregar_dados_do_csv()

@app.get("/api/tasks")
def get_tasks(background_tasks: BackgroundTasks):
    agora = time.time()
    if agora - ULTIMA_ATUALIZACAO > TEMPO_CACHE_SEGUNDOS:
        background_tasks.add_task(carregar_dados_do_csv)
    return {"tasks": CACHE_TAREFAS}

@app.post("/api/save")
def save_task(payload: dict):
    try:
        res = requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
        carregar_dados_do_csv()
        return JSONResponse(content={"status": "SUCCESS", "sheet_response": res.json()})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "ERROR", "message": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
