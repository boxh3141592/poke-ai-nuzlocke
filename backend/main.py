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

    prompt = f"""
    Eres un experto en Pokémon competitivo.
    EQUIPO: {party}
    INVENTARIO: {inventory}
    CAJA: {box}

    Diseña la mejor estrategia de 6 Pokémon.
    Responde SOLO y EXCLUSIVAMENTE con un JSON válido. No escribas nada antes ni después del JSON.
    
    Formato JSON:
    {{
      "analysis_summary": "Consejo breve...",
      "team": [ 
        {{ "species": "Nombre", "role": "Rol", "ability": "Habilidad", "item_suggestion": "Objeto", "moves": ["M1", "M2", "M3", "M4"], "reason": "Razón" }} 
      ]
    }}
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