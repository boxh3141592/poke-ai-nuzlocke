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

# Base de datos en memoria (ID -> Datos)
sessions_db = {} 

def process_strategy_in_background(session_id: str, data: dict):
    global sessions_db
    print(f"🧠 Procesando sesión: {session_id}")
    
    # Marcamos como "pensando"
    sessions_db[session_id] = {"status": "thinking"}

    # VERIFICACIÓN DE SEGURIDAD: ¿Hay Pokémon?
    party = data.get('party', [])
    box = data.get('box', [])
    
    if not party and not box:
        # Si no hay Pokémon, no gastamos IA, devolvemos aviso directo.
        sessions_db[session_id] = {
            "analysis_summary": "⚠️ No se encontraron Pokémon en los datos recibidos. Asegúrate de tener al menos un Pokémon en tu equipo o PC antes de pedir una estrategia.",
            "team": []
        }
        print("⚠️ Datos vacíos recibidos.")
        return

    prompt = f"""
    Eres un experto en mecánica de Pokémon.
    EQUIPO: {party}
    INVENTARIO: {data.get('inventory')}
    CAJA: {box}

    Crea una estrategia competitiva (Roles, Objetos, Movimientos) para este equipo.
    Responde SOLO en JSON con este formato:
    {{
      "analysis_summary": "Resumen...",
      "team": [ {{ "species": "Nombre", "role": "Rol", "item_suggestion": "Objeto", "moves": ["M1", "M2", "M3", "M4"], "reason": "Razón" }} ]
    }}
    """

    try:
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        new_analysis = json.loads(response.text)
        
        # Inyectar datos originales para el frontend
        new_analysis["raw_party_data"] = party
        new_analysis["inventory_data"] = data.get('inventory', [])
        
        sessions_db[session_id] = new_analysis
        
    except Exception as e:
        print(f"Error IA: {e}")
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