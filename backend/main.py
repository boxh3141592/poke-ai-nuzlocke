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

    prompt = f"""
    Eres un experto en Nuzlocke.
    
    MISIÓN:
    Construye el MEJOR equipo de 6 Pokémon usando lo que tengo en el equipo y en la caja.
    
    REGLAS ESTRICTAS PARA MOVIMIENTOS:
    1. Tanto para los Pokémon del equipo como para los que saques de la CAJA:
       REVISA SIEMPRE EL CAMPO "move_pool".
    2. El "move_pool" contiene ataques que saben, que pueden recordar y MTs compatibles.
    3. ¡NO DEJES POKÉMON SIN ATAQUES! Selecciona siempre 4 ataques del pool.
    4. Si un Pokémon viene de la caja, ármalo desde cero con los mejores ataques del pool.

    DATOS:
    EQUIPO ACTUAL ({len(party)}): {json.dumps(party)}
    CAJA PC ({len(box)}): {json.dumps(box)}
    INVENTARIO: {inventory}

    FORMATO DE RESPUESTA (JSON PURO):
    {{
      "analysis_summary": "Resumen de cambios (ej: 'Saqué a Gible de la caja y le enseñé Terremoto usando tu MT')...",
      "team": [ 
        {{ 
           "species": "Nombre", 
           "role": "Rol", 
           "ability": "Habilidad", 
           "item_suggestion": "Objeto", 
           "moves": ["M1", "M2", "M3", "M4"], 
           "reason": "Razón estratégica." 
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
        
        # --- CAMBIO CRÍTICO AQUÍ ---
        # Unimos Party + Box para que el Frontend tenga TODAS las definiciones de ataques/stats
        # Así, si entra uno de la caja, la web sabrá mostrar sus detalles.
        new_analysis["raw_party_data"] = party + box 
        
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