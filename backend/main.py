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

# Configuración de permisos (CORS) para que Vercel y RPG Maker puedan entrar
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base de datos en memoria (ID -> Datos)
sessions_db = {} 

# --- ✅ NUEVO: ENDPOINT "KEEP ALIVE" ---
# Este es el que usará UptimeRobot para mantener despierto al servidor
@app.get("/")
def keep_alive():
    return {"status": "online", "message": "GeminiLink backend is running!"}

# --- LÓGICA DE IA EN SEGUNDO PLANO ---
def process_strategy_in_background(session_id: str, data: dict):
    global sessions_db
    print(f"🧠 Procesando sesión: {session_id}")
    
    # 1. Marcamos estado: Pensando
    sessions_db[session_id] = {"status": "thinking"}

    # 2. Verificación de Seguridad: ¿Hay datos reales?
    party = data.get('party', [])
    box = data.get('box', [])
    inventory = data.get('inventory', [])
    
    if not party and not box:
        sessions_db[session_id] = {
            "analysis_summary": "⚠️ No se detectaron Pokémon en el equipo ni en la caja. Asegúrate de tener al menos un Pokémon capturado.",
            "team": []
        }
        print("⚠️ Datos vacíos recibidos (Equipo vacío).")
        return

    # 3. Prompt para Gemini
    prompt = f"""
    Eres un experto en mecánica de Pokémon (Nuzlockes/Fan-Games).
    
    CONTEXTO DEL JUGADOR:
    - EQUIPO ACTUAL: {party}
    - INVENTARIO: {inventory}
    - CAJA (PC): {box}

    TU MISIÓN:
    Diseña la mejor estrategia posible con estos recursos.
    
    REGLAS:
    - Usa los datos técnicos (Potencia, Precisión) que te doy en el JSON.
    - Si el equipo es débil, sugiere cambios usando Pokémon de la CAJA.
    - Asigna objetos del INVENTARIO si son útiles.

    FORMATO DE RESPUESTA (JSON PURO):
    {{
      "analysis_summary": "Consejo general estratégico y breve...",
      "team": [ 
        {{ 
            "species": "Nombre", 
            "role": "Atacante Físico/Tanque/Support/etc", 
            "item_suggestion": "Objeto o 'Nada'", 
            "moves": ["Mov1", "Mov2", "Mov3", "Mov4"], 
            "reason": "Por qué esta configuración es buena" 
        }} 
      ]
    }}
    """

    try:
        # Usamos el modelo Flash 1.5 que es rápido y barato/gratis
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        
        new_analysis = json.loads(response.text)
        
        # 4. Inyectamos los datos originales para que el Frontend pueda mostrar Iconos y Tooltips
        new_analysis["raw_party_data"] = party
        new_analysis["inventory_data"] = inventory
        
        # 5. Guardamos en la "Base de Datos"
        sessions_db[session_id] = new_analysis
        print(f"✅ Estrategia guardada para ID: {session_id}")
        
    except Exception as e:
        print(f"❌ Error IA: {e}")
        sessions_db[session_id] = {"error": "Error al procesar la estrategia con la IA."}

# --- ENDPOINT 1: RECIBIR DATOS (Desde RPG Maker) ---
@app.post("/update-roster")
async def update_roster(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        session_id = payload.get("session_id")
        team_data = payload.get("team")
        
        if not session_id:
            return {"status": "error", "message": "Falta el session_id"}

        # Lanzamos la tarea a segundo plano para responder rápido al juego
        background_tasks.add_task(process_strategy_in_background, session_id, team_data)
        
        return {"status": "queued", "id": session_id}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- ENDPOINT 2: ENTREGAR DATOS (Hacia Vercel/Web) ---
@app.get("/get-analysis")
async def get_analysis(id: str = None):
    if not id:
        return {"error": "Falta el ID de sesión"}
    
    # Buscamos en memoria, si no existe devolvemos "waiting"
    return sessions_db.get(id, {"status": "waiting"})