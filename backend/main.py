from fastapi import FastAPI, Request, BackgroundTasks
import json
from fastapi.middleware.cors import CORSMiddleware
import os
from groq import Groq

# --- CONFIGURACIÓN ---
api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key)

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
    return {"status": "online", "message": "Backend running with Groq Llama 3.3!"}

# --- DIAGNÓSTICO PARA GROQ ---
# Si vuelve a fallar, entra a /models para ver los nombres nuevos
@app.get("/models")
def list_models():
    try:
        # Groq también tiene una función para listar modelos
        models = client.models.list()
        # Extraemos solo los IDs de los modelos
        nombres = [m.id for m in models.data]
        return {"available_models": nombres}
    except Exception as e:
        return {"error": str(e)}

def process_strategy_in_background(session_id: str, data: dict):
    global sessions_db
    print(f"🧠 Procesando sesión con Groq: {session_id}")
    
    sessions_db[session_id] = {"status": "thinking"}

    party = data.get('party', [])
    box = data.get('box', [])
    inventory = data.get('inventory', [])
    
    if not party and not box:
        sessions_db[session_id] = {
            "analysis_summary": "⚠️ No se encontraron Pokémon.",
            "team": []
        }
        return

 # ... (Imports y Configuración igual que antes) ...

    prompt = f"""
    Eres el mejor entrenador Pokémon del mundo experto en Nuzlockes.
    
    Tengo un equipo Pokémon y necesito que optimices sus movimientos.
    
    DATOS RECIBIDOS:
    1. EQUIPO ("party"): Lista de mis Pokémon. Cada uno tiene un campo "move_pool".
    2. MOVE POOL: Es la lista de TODOS los ataques que ese Pokémon puede aprender (incluye los que ya tiene, los que olvidó y las MTs de mi mochila).
    
    TU MISIÓN:
    Para CADA Pokémon del equipo, elige los 4 MEJORES movimientos posibles sacados de su "move_pool".
    
    REGLAS:
    - NO te limites a los ataques que ya tiene. Revisa todo el "move_pool".
    - Si encuentras un ataque en el "move_pool" que es mejor que uno actual (ej: tiene Lanzallamas en pool pero Arañazo equipado), ¡Dímelo!
    - Explica en "reason" qué cambios hiciste (ej: "Sustituí Arañazo por Lanzallamas porque tienes la MT").

    Responde SOLO JSON válido:
    {{
      "analysis_summary": "Resumen general del estado del equipo...",
      "team": [ 
        {{ 
           "species": "Nombre", 
           "role": "Atacante Físico / Tanque / etc", 
           "ability": "Nombre Habilidad", 
           "item_suggestion": "Objeto sugerido", 
           "moves": ["Ataque 1", "Ataque 2", "Ataque 3", "Ataque 4"], 
           "reason": "Explica la estrategia y si cambiaste ataques usando el move_pool." 
        }} 
      ]
    }}
    
    AQUÍ ESTÁN LOS DATOS RAW DEL JUEGO:
    {json.dumps(party)}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente que solo habla en JSON válido."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            # --- CAMBIO IMPORTANTE: MODELO ACTUALIZADO ---
            # Usamos la versión 3.3 Versatile, que es la actual.
            # Si en el futuro falla, revisa /models
            model="llama-3.3-70b-versatile", 
            temperature=0.5,
            response_format={"type": "json_object"}, 
        )

        response_content = chat_completion.choices[0].message.content
        new_analysis = json.loads(response_content)
        
        new_analysis["raw_party_data"] = party
        new_analysis["inventory_data"] = inventory
        
        sessions_db[session_id] = new_analysis
        print(f"✅ Estrategia lista (Groq): {session_id}")
        
    except Exception as e:
        print(f"❌ Error Groq: {e}")
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