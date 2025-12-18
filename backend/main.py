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

# Base de datos en memoria (ID -> Datos)
sessions_db = {} 

# --- ENDPOINT ANTI-SUEÑO (KEEP ALIVE) ---
@app.get("/")
def keep_alive():
    return {"status": "online", "message": "GeminiLink backend is running!"}

# --- LÓGICA DE IA ---
def process_strategy_in_background(session_id: str, data: dict):
    global sessions_db
    print(f"🧠 Procesando sesión: {session_id}")
    
    sessions_db[session_id] = {"status": "thinking"}

    party = data.get('party', [])
    box = data.get('box', [])
    inventory = data.get('inventory', [])
    
    # Verificación de seguridad
    if not party and not box:
        sessions_db[session_id] = {
            "analysis_summary": "⚠️ No se encontraron Pokémon. Asegúrate de tener al menos uno en el equipo o PC.",
            "team": []
        }
        print("⚠️ Datos vacíos recibidos.")
        return

    prompt = f"""
    Eres un experto en mecánica de Pokémon.
    EQUIPO: {party}
    INVENTARIO: {inventory}
    CAJA: {box}

    Diseña la mejor estrategia posible.
    Responde SOLO en JSON con este formato:
    {{
      "analysis_summary": "Consejo breve...",
      "team": [ 
        {{ "species": "Nombre", "role": "Rol", "item_suggestion": "Objeto", "moves": ["M1", "M2", "M3", "M4"], "reason": "Razón" }} 
      ]
    }}
    """

    try:
        # --- CORRECCIÓN CRÍTICA AQUÍ ---
        # Usamos la versión específica '-001' que es más estable y evita el error 404
        response = client.models.generate_content(
            model='gemini-1.5-flash-001',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        
        new_analysis = json.loads(response.text)
        
        # Inyectar datos para el frontend
        new_analysis["raw_party_data"] = party
        new_analysis["inventory_data"] = inventory
        
        sessions_db[session_id] = new_analysis
        print(f"✅ Estrategia generada con éxito para ID: {session_id}")
        
    except Exception as e:
        print(f"❌ Error CRÍTICO IA: {e}")
        sessions_db[session_id] = {"error": f"Error de IA: {str(e)}"}

# --- ENDPOINTS API ---
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