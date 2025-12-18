from fastapi import FastAPI, Request, BackgroundTasks
from google import genai
from google.genai import types
import json
from fastapi.middleware.cors import CORSMiddleware
import os

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions_db = {} 

@app.get("/")
def keep_alive():
    return {"status": "online", "message": "GeminiLink backend is running!"}

def process_strategy_in_background(session_id: str, data: dict):
    global sessions_db
    print(f"🧠 Procesando sesión: {session_id}")
    
    sessions_db[session_id] = {"status": "thinking"}

    party = data.get('party', [])
    box = data.get('box', [])
    inventory = data.get('inventory', [])
    
    if not party and not box:
        sessions_db[session_id] = {
            "analysis_summary": "⚠️ No tienes Pokémon. Captura algunos primero.",
            "team": []
        }
        return

    # --- PROMPT ACTUALIZADO (PIDE HABILIDAD) ---
    prompt = f"""
    Eres el mejor estratega Pokémon.
    
    RECURSOS:
    1. EQUIPO ACTUAL: {party}
    2. CAJA: {box}
    3. INVENTARIO: {inventory}

    MISIÓN: Construye el mejor equipo de 6. Rellena huecos con la caja si es necesario.
    
    FORMATO JSON OBLIGATORIO:
    {{
      "analysis_summary": "Resumen breve...",
      "team": [ 
        {{ 
           "species": "Nombre", 
           "role": "Rol", 
           "ability": "Nombre Habilidad",  <-- ESTO ES LO NUEVO
           "item_suggestion": "Objeto", 
           "moves": ["M1", "M2", "M3", "M4"], 
           "reason": "Razón" 
        }} 
      ]
    }}
    """

    try:
        response = client.models.generate_content(
            model='gemini-flash-latest', 
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        
        new_analysis = json.loads(response.text)
        new_analysis["raw_party_data"] = party
        new_analysis["inventory_data"] = inventory
        
        sessions_db[session_id] = new_analysis
        print(f"✅ Estrategia con Habilidades lista: {session_id}")
        
    except Exception as e:
        print(f"❌ Error IA: {e}")
        sessions_db[session_id] = {"error": str(e)}

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