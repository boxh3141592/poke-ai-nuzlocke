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

# --- HERRAMIENTA DE DIAGNÓSTICO (NUEVO) ---
# Si algo falla, entra a tuweb.com/models para ver qué nombres acepta Google
@app.get("/models")
def list_models():
    try:
        # Esto nos dirá la verdad sobre qué modelos están disponibles
        m = client.models.list()
        # Filtramos solo los que sirven para generar contenido
        nombres = [model.name for model in m if "generateContent" in model.supported_generation_methods]
        return {"available_models": nombres}
    except Exception as e:
        return {"error": str(e)}

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
        # --- EL CAMBIO CLAVE ---
        # Usamos la versión '002' que es la estable actual de la serie 1.5.
        # Esta tiene 1500 peticiones gratis al día y NO es la 2.5 experimental.
        response = client.models.generate_content(
            model='gemini-1.5-flash-002', 
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
        # Guardamos el error para que lo veas en la web si pasa algo
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