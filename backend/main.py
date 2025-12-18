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

# --- LÓGICA DE IA ---
def process_strategy_in_background(session_id: str, data: dict):
    global sessions_db
    print(f"🧠 Procesando sesión con Groq: {session_id}")
    
    # --- PROTECCIÓN CONTRA EL ERROR DE NONETYPE ---
    if not data:
        print("❌ Error: Se recibieron datos vacíos en process_strategy_in_background")
        sessions_db[session_id] = {"error": "Error interno: Datos vacíos recibidos del juego."}
        return

    sessions_db[session_id] = {"status": "thinking"}

    party = data.get('party', [])
    box = data.get('box', [])
    inventory = data.get('inventory', [])
    
    if not party and not box:
        sessions_db[session_id] = {
            "analysis_summary": "⚠️ No se encontraron datos de Pokémon.",
            "team": []
        }
        return

    prompt = f"""
    Eres el mejor entrenador Pokémon del mundo, experto en retos Nuzlocke.
    
    OBJETIVO:
    Analiza mi equipo y construye la mejor estrategia de 6 Pokémon para sobrevivir.
    
    INFORMACIÓN CLAVE:
    1. Recibirás una lista de Pokémon en "party".
    2. Cada Pokémon tiene un campo "move_pool" con TODOS sus ataques posibles (actuales + recordables + MTs mochila).
    
    INSTRUCCIONES OBLIGATORIAS:
    - NO te limites a los ataques actuales.
    - REVISA el "move_pool". Si ves un ataque mejor ahí, ¡Sugiérelo!
    - Explica en "reason" si cambiaste ataques usando el pool (ej: "Enseña Rayo Hielo usando MT").

    DATOS DEL JUEGO:
    EQUIPO ACTUAL: {json.dumps(party)}
    INVENTARIO: {inventory}
    CAJA: {box}

    FORMATO JSON OBLIGATORIO:
    {{
      "analysis_summary": "Resumen estratégico...",
      "team": [ 
        {{ 
           "species": "Nombre", 
           "role": "Rol", 
           "ability": "Habilidad", 
           "item_suggestion": "Objeto", 
           "moves": ["M1", "M2", "M3", "M4"], 
           "reason": "Explicación de la estrategia y uso del move_pool." 
        }} 
      ]
    }}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente que solo responde en JSON válido."
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

# --- ENDPOINT CORREGIDO ---
@app.post("/update-roster")
async def update_roster(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        session_id = payload.get("session_id")
        
        # --- AQUÍ ESTABA EL ERROR ANTES ---
        # Antes: team_data = payload.get("team") -> Esto daba None
        # Ahora: Usamos 'payload' directamente porque Ruby envía los datos en la raíz
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