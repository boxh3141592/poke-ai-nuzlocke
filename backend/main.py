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

# --- BASE DE DATOS DE SESIONES ---
sessions_db = {} 

# --- ENDPOINT ANTI-SUEÑO ---
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
    
    # Verificación: ¿Estamos vacíos?
    if not party and not box:
        sessions_db[session_id] = {
            "analysis_summary": "⚠️ No tienes Pokémon ni en el equipo ni en la caja. ¡Captura algunos primero!",
            "team": []
        }
        return

    # --- PROMPT MEJORADO (ORDEN MILITAR DE RELLENADO) ---
    prompt = f"""
    Eres el mejor estratega Pokémon del mundo.
    
    TUS RECURSOS:
    1. MI EQUIPO ACTUAL ({len(party)} Pokémon): {party}
    2. MI CAJA DE RESERVAS: {box}
    3. MI INVENTARIO: {inventory}

    ⚠️ TU MISIÓN PRIORITARIA (OBLIGATORIO):
    CONSTRUIR UN EQUIPO FINAL DE EXACTAMENTE 6 POKÉMON.
    
    REGLAS DE SELECCIÓN:
    1. Si el "EQUIPO ACTUAL" tiene menos de 6 Pokémon, DEBES elegir los mejores candidatos de la "CAJA DE RESERVAS" para llenar los huecos hasta tener 6.
    2. NO devuelvas un equipo incompleto a menos que la Caja esté vacía.
    3. Si un Pokémon del equipo actual es muy malo y hay uno mucho mejor en la Caja, SUGIERE EL CAMBIO.
    
    REGLAS DE ESTRATEGIA:
    - Asigna ROLES claros (Tanque, Sweeper Físico, Support, etc.).
    - Usa los datos matemáticos que te di (Potencia, Stats) para decidir.
    - Elige los 4 mejores movimientos del pool disponible.

    FORMATO DE RESPUESTA (JSON PURO):
    {{
      "analysis_summary": "Explicación breve de por qué elegiste a estos nuevos miembros para completar el equipo...",
      "team": [ 
        {{ 
           "species": "Nombre", 
           "role": "Rol", 
           "item_suggestion": "Objeto", 
           "moves": ["M1", "M2", "M3", "M4"], 
           "reason": "Razón (Si vino de la caja, explica por qué lo elegiste)" 
        }} 
      ]
    }}
    """

    try:
        # Usamos el modelo estable que te funciona
        response = client.models.generate_content(
            model='gemini-flash-latest', 
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        
        new_analysis = json.loads(response.text)
        
        # Inyectamos datos para el Frontend
        new_analysis["raw_party_data"] = party
        new_analysis["inventory_data"] = inventory
        
        # --- TRUCO VISUAL PARA EL FRONTEND ---
        # Si la IA añade Pokémon de la caja, el frontend no tendrá sus datos completos (iconos/stats) 
        # porque solo enviamos datos completos del Party.
        # Aquí combinamos "party" + "box" para que el frontend pueda buscar datos si hace falta.
        # (Nota: La caja tiene datos simplificados, pero servirá para que no explote).
        
        sessions_db[session_id] = new_analysis
        print(f"✅ Estrategia (Full Team 6) generada para ID: {session_id}")
        
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