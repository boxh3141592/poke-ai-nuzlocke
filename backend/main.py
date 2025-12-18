from fastapi import FastAPI, Request, BackgroundTasks
from google import genai
from google.genai import types
import json
from fastapi.middleware.cors import CORSMiddleware
import os

# --- CONFIGURACIÓN ---
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base de datos en memoria
sessions_db = {} 

# --- ENDPOINT ANTI-SUEÑO ---
@app.get("/")
def keep_alive():
    return {"status": "online", "message": "GeminiLink backend is running!"}

# --- HERRAMIENTA DE DIAGNÓSTICO ---
# La dejamos por si acaso, es muy útil
@app.get("/models")
def list_models():
    try:
        m = client.models.list()
        nombres = [str(model.name).replace("models/", "") for model in m]
        return {"available_models": nombres}
    except Exception as e:
        return {"error": f"Error listando modelos: {str(e)}"}

# --- LÓGICA DE IA ---
def process_strategy_in_background(session_id: str, data: dict):
    global sessions_db
    print(f"🧠 Procesando sesión: {session_id}")
    
    sessions_db[session_id] = {"status": "thinking"}

    party = data.get('party', [])
    box = data.get('box', [])
    inventory = data.get('inventory', [])
    
    if not party and not box:
        sessions_db[session_id] = {
            "analysis_summary": "⚠️ No se encontraron Pokémon. Asegúrate de tener al menos uno en el equipo.",
            "team": []
        }
        return

    prompt = f"""
    Eres un experto en mecánica de Pokémon.
    EQUIPO: {party}
    INVENTARIO: {inventory}
    CAJA: {box}

    Diseña la mejor estrategia posible. Rellena el equipo hasta 6 si es necesario.
    Responde SOLO en JSON:
    {{
      "analysis_summary": "Consejo breve...",
      "team": [ 
        {{ "species": "Nombre", "role": "Rol", "ability": "Habilidad", "item_suggestion": "Objeto", "moves": ["M1", "M2", "M3", "M4"], "reason": "Razón" }} 
      ]
    }}
    """

    try:
        # --- EL CAMBIO DEFINITIVO ---
        # Usamos 'gemini-2.0-flash' porque confirmamos que ESTÁ en tu lista.
        # Es más rápido y mejor que el 1.5, y no tiene el límite estricto del 2.5.
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        
        new_analysis = json.loads(response.text)
        new_analysis["raw_party_data"] = party
        new_analysis["inventory_data"] = inventory
        
        sessions_db[session_id] = new_analysis
        print(f"✅ Estrategia lista: {session_id}")
        
    except Exception as e:
        print(f"❌ Error IA: {e}")
        sessions_db[session_id] = {"error": f"Error técnico: {str(e)}"}

@app.post("/update-roster")
async def update_roster(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        session_id = payload.get("session_id")
        team_data = payload.get("team")
        
        if not session_id: return {"status": "error", "message": "No ID"}

        background_tasks.add_task(process_strategy_in_background, session_id, team_data)
        return {"status": "queued", "id": session_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/get-analysis")
async def get_analysis(id: str = None):
    if not id: return {"error": "Falta ID"}
    return sessions_db.get(id, {"status": "waiting"})