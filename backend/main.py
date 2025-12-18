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

# --- BASE DE DATOS EN MEMORIA (DICCIONARIO DE SESIONES) ---
# Aquí guardamos los datos de cada jugador por separado
sessions_db = {} 

# --- ENDPOINT ANTI-SUEÑO (KEEP ALIVE) ---
# Esto es para que UptimeRobot mantenga el servidor despierto
@app.get("/")
def keep_alive():
    return {"status": "online", "message": "GeminiLink backend is running!"}

# --- LÓGICA DE IA EN SEGUNDO PLANO ---
def process_strategy_in_background(session_id: str, data: dict):
    global sessions_db
    print(f"🧠 Procesando sesión: {session_id}")
    
    # 1. Marcamos estado: Pensando
    sessions_db[session_id] = {"status": "thinking"}

    # 2. Extraemos los datos
    party = data.get('party', [])
    box = data.get('box', [])
    inventory = data.get('inventory', [])
    
    # 3. Verificación de Seguridad: ¿Hay datos reales?
    if not party and not box:
        sessions_db[session_id] = {
            "analysis_summary": "⚠️ No se detectaron Pokémon en el equipo ni en la caja. Asegúrate de tener al menos un Pokémon capturado.",
            "team": []
        }
        print(f"⚠️ Datos vacíos recibidos para sesión {session_id}.")
        return

    # 4. Prompt (Tu versión original)
    prompt = f"""
    Eres un experto en mecánica de Pokémon (Nuzlockes/Fan-Games).
    HE EXTRAÍDO LOS DATOS INTERNOS (PBS) DEL JUEGO.
    
    1. EQUIPO (Party): {party}
    2. INVENTARIO: {inventory}
    3. RESERVA (PC): {box}

    TU MISIÓN:
    Diseña la estrategia perfecta basándote en la matemática de los datos enviados.
    
    REGLAS:
    - DATOS REALES: Usa la potencia/precisión/descripción que te envío, no lo que creas saber.
    - MOVIMIENTOS: Elige los 4 mejores del 'move_pool'. Prioriza STAB.
    - OBJETOS: Asigna objetos del inventario útiles según descripción.
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
        # --- AQUÍ ESTÁ LA CLAVE ---
        # He vuelto a poner EXACTAMENTE el modelo que usabas tú y que funcionaba.
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        
        new_analysis = json.loads(response.text)
        
        # 5. Inyectamos los datos originales (para Iconos y Tooltips en el Frontend)
        new_analysis["raw_party_data"] = party
        new_analysis["inventory_data"] = inventory
        
        # 6. Guardamos en el diccionario usando el ID DE SESIÓN
        sessions_db[session_id] = new_analysis
        print(f"✅ Estrategia guardada para ID: {session_id}")
        
    except Exception as e:
        print(f"❌ Error IA en sesión {session_id}: {e}")
        sessions_db[session_id] = {"error": f"Error de IA: {str(e)}"}

# --- ENDPOINT 1: RECIBIR DATOS (Desde RPG Maker) ---
@app.post("/update-roster")
async def update_roster(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        
        # Leemos el ID que nos manda el juego
        session_id = payload.get("session_id")
        team_data = payload.get("team")
        
        if not session_id:
            return {"status": "error", "message": "Falta el session_id"}

        # Lanzamos la tarea a segundo plano pasando el ID
        background_tasks.add_task(process_strategy_in_background, session_id, team_data)
        
        return {"status": "queued", "id": session_id}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- ENDPOINT 2: ENTREGAR DATOS (Hacia la Web) ---
@app.get("/get-analysis")
async def get_analysis(id: str = None):
    if not id:
        return {"error": "Falta el ID de sesión"}
    
    # Buscamos en el diccionario. Si no existe, devolvemos 'waiting'
    return sessions_db.get(id, {"status": "waiting"})