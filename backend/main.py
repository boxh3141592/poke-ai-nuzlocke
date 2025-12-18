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

@app.get("/models")
def list_models():
    try:
        models = client.models.list()
        nombres = [m.id for m in models.data]
        return {"available_models": nombres}
    except Exception as e:
        return {"error": str(e)}

# --- LÓGICA DE IA (CEREBRO MEJORADO) ---
def process_strategy_in_background(session_id: str, data: dict):
    global sessions_db
    print(f"🧠 Procesando sesión con Groq: {session_id}")
    
    if not data:
        sessions_db[session_id] = {"error": "Error: Datos vacíos."}
        return

    sessions_db[session_id] = {"status": "thinking"}

    party = data.get('party', [])
    box = data.get('box', [])
    inventory = data.get('inventory', [])
    
    if not party and not box:
        sessions_db[session_id] = {
            "analysis_summary": "⚠️ No se encontraron Pokémon ni en equipo ni en caja.",
            "team": []
        }
        return

    # --- PROMPT MILITAR PARA RELLENAR EQUIPO ---
    prompt = f"""
    Eres un experto en Nuzlocke. TU MISIÓN ES CONSTRUIR UN EQUIPO COMPLETO DE 6 POKÉMON.
    
    REGLAS DE ORO (IMPORTANTE):
    1.  **ANÁLISIS DE CANTIDAD:** Cuenta cuántos Pokémon hay en el "EQUIPO ACTUAL".
    2.  **RELLENO OBLIGATORIO:** Si hay MENOS de 6 Pokémon en el equipo actual, ESTÁS OBLIGADO a buscar en la "CAJA" los mejores candidatos para rellenar los huecos hasta llegar a 6.
    3.  **PRIORIDAD:** Mantén a los del equipo actual (a menos que sean terribles), y completa el resto con la caja.
    4.  **MOVE POOL:** Usa el campo "move_pool" para sugerir ataques óptimos (incluyendo MTs y recordar movimientos).

    DATOS:
    EQUIPO ACTUAL ({len(party)} Pokémon): {json.dumps(party)}
    CAJA DE PC ({len(box)} Pokémon): {json.dumps(box)}
    INVENTARIO: {inventory}

    FORMATO DE RESPUESTA (JSON PURO):
    {{
      "analysis_summary": "He mantenido tus {len(party)} Pokémon y he añadido X de la caja para completar el equipo...",
      "team": [ 
        {{ 
           "species": "Nombre", 
           "role": "Rol", 
           "ability": "Habilidad", 
           "item_suggestion": "Objeto", 
           "moves": ["M1", "M2", "M3", "M4"], 
           "reason": "Explicación (Si vino de la caja, dilo aquí)." 
        }} 
      ]
    }}
    """
    # (El resto de la llamada a la API sigue igual...)
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente que solo responde en JSON válido y siempre completa equipos de 6."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
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
        team_data = payload 
        
        if not session_id: 
            import uuid
            session_id = str(uuid.uuid4())[:8]

        background_tasks.add_task(process_strategy_in_background, session_id, team_data)
        
        return {"status": "queued", "id": session_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/get-analysis")
async def get_analysis(id: str = None):
    if not id: return {"error": "Falta ID"}
    return sessions_db.get(id, {"status": "waiting"})