# main.py (Versión con Soporte Multi-Sesión)
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

# --- MEMORIA RAM DEL SERVIDOR (Multi-Usuario) ---
# Ahora es un diccionario donde la clave es el ID de sesión
sessions_db = {} 

# --- FUNCIÓN EN SEGUNDO PLANO ---
def process_strategy_in_background(session_id: str, data: dict):
    global sessions_db
    print(f"🧠 Gemini analizando para la sesión: {session_id}")
    
    # Marcamos como "procesando"
    sessions_db[session_id] = {"status": "thinking", "message": "La IA está pensando tu estrategia..."}

    prompt = f"""
    Eres un experto en mecánica de Pokémon (Nuzlockes/Fan-Games).
    HE EXTRAÍDO LOS DATOS INTERNOS (PBS) DEL JUEGO.
    
    1. EQUIPO (Party): {data.get('party')}
    2. INVENTARIO: {data.get('inventory')}
    3. RESERVA (PC): {data.get('box')}

    TU MISIÓN:
    Diseña la estrategia perfecta basándote en la matemática de los datos enviados.
    
    REGLAS:
    - DATOS REALES: Usa la potencia/precisión/descripción que te envío.
    - MOVIMIENTOS: Elige los 4 mejores del 'move_pool'. Prioriza STAB.
    - OBJETOS: Asigna objetos del inventario útiles.
    - ROLES: Define roles competitivos.

    FORMATO JSON:
    {{
      "analysis_summary": "Consejo general...",
      "team": [
        {{
          "species": "Nombre",
          "role": "Rol",
          "item_suggestion": "Objeto",
          "moves": ["M1", "M2", "M3", "M4"],
          "ability": "Nombre",
          "reason": "Explicación"
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
        
        # Inyectamos datos crudos para el frontend
        if "party" in data: new_analysis["raw_party_data"] = data["party"]
        if "inventory" in data: new_analysis["inventory_data"] = data["inventory"]
        
        # Guardamos en la base de datos CON EL ID
        sessions_db[session_id] = new_analysis
        print(f"✅ Estrategia lista para ID {session_id}")
        
    except Exception as e:
        print(f"❌ Error en sesión {session_id}: {e}")
        sessions_db[session_id] = {"error": str(e)}

# --- ENDPOINT DE RECEPCIÓN ---
@app.post("/update-roster")
async def update_roster(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        
        # Obtenemos los datos y el ID
        session_id = payload.get("session_id")
        team_data = payload.get("team")
        
        if not session_id or not team_data:
            return {"status": "error", "message": "Faltan datos o ID"}

        # Lanzamos la tarea con el ID específico
        background_tasks.add_task(process_strategy_in_background, session_id, team_data)
        
        return {"status": "queued", "id": session_id}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- ENDPOINT DE CONSULTA (AHORA PIDE ID) ---
@app.get("/get-analysis")
async def get_analysis(id: str = None):
    # Si no nos dan ID, error
    if not id:
        return {"error": "Falta el ID de sesión"}
    
    # Buscamos en la memoria
    data = sessions_db.get(id)
    
    if not data:
        return {"status": "waiting", "message": "Esperando datos o ID inválido"}
        
    return data