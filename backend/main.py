from fastapi import FastAPI, Request, BackgroundTasks
import json
from fastapi.middleware.cors import CORSMiddleware
import os
from groq import Groq

# --- CONFIGURACIÓN ---
# Asegúrate de tener la variable GROQ_API_KEY en Render
api_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key)

app = FastAPI()

# Permisos CORS para que el Frontend (React) pueda hablar con el Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base de datos temporal en memoria RAM
sessions_db = {} 

# --- ENDPOINT 1: MANTENER VIVO ---
# UptimeRobot llama a este link para que Render no se duerma
@app.get("/")
def keep_alive():
    return {"status": "online", "message": "Backend running with Groq Llama 3.3!"}

# --- ENDPOINT 2: DIAGNÓSTICO ---
# Útil si Groq cambia nombres de modelos en el futuro. Entra a /models para ver la lista.
@app.get("/models")
def list_models():
    try:
        models = client.models.list()
        nombres = [m.id for m in models.data]
        return {"available_models": nombres}
    except Exception as e:
        return {"error": str(e)}

# --- LÓGICA DE IA (CEREBRO) ---
def process_strategy_in_background(session_id: str, data: dict):
    global sessions_db
    print(f"🧠 Procesando sesión con Groq: {session_id}")
    
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

    # --- EL PROMPT MAESTRO (Aquí está la magia) ---
    # Le explicamos a la IA cómo usar el 'move_pool' que envía tu script de Ruby.
    prompt = f"""
    Eres el mejor entrenador Pokémon del mundo, experto en retos Nuzlocke.
    
    OBJETIVO:
    Analiza mi equipo y construye la mejor estrategia de 6 Pokémon para sobrevivir.
    
    INFORMACIÓN CLAVE SOBRE LOS DATOS:
    1. Recibirás una lista de Pokémon en "party".
    2. Cada Pokémon tiene un campo llamado "move_pool".
    3. "move_pool" contiene TODOS los ataques que ese Pokémon puede usar (incluye los que ya tiene, los que puede recordar por nivel y las MTs que tengo en la mochila).
    
    INSTRUCCIONES OBLIGATORIAS:
    - NO te limites a los 4 ataques que el Pokémon tiene equipados actualmente.
    - REVISA el "move_pool" de cada Pokémon. Si ves un ataque mejor ahí (por potencia, cobertura o utilidad), ¡Sugiérelo!
    - Si sugieres un ataque que el Pokémon no tiene equipado, explícalo en la "reason" (ej: "Enseña Rayo Hielo usando tu MT").
    - Elige una Habilidad y un Objeto basándote en los datos recibidos.

    DATOS DEL JUEGO:
    EQUIPO ACTUAL: {json.dumps(party)}
    INVENTARIO: {inventory}
    CAJA: {box}

    FORMATO DE RESPUESTA (JSON PURO):
    Responde SOLO y EXCLUSIVAMENTE con un JSON válido. No añadas texto antes ni después.
    {{
      "analysis_summary": "Resumen estratégico general (ej: 'Tu equipo es fuerte en ataque especial pero débil a Tierra. Te recomiendo...')",
      "team": [ 
        {{ 
           "species": "Nombre", 
           "role": "Rol (ej: Muralla Física, Sweeper Especial)", 
           "ability": "Nombre Habilidad", 
           "item_suggestion": "Objeto sugerido", 
           "moves": ["Ataque 1", "Ataque 2", "Ataque 3", "Ataque 4"], 
           "reason": "Explica por qué elegiste este set y si debe aprender movimientos nuevos del pool." 
        }} 
      ]
    }}
    """

    try:
        # Llamada a Groq (Llama 3.3)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente estratégico que solo responde en JSON válido."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile", # Modelo potente y actual
            temperature=0.5,
            response_format={"type": "json_object"}, 
        )

        response_content = chat_completion.choices[0].message.content
        new_analysis = json.loads(response_content)
        
        # Guardamos datos crudos para que el Frontend pueda mostrar detalles al pasar el mouse
        new_analysis["raw_party_data"] = party
        new_analysis["inventory_data"] = inventory
        
        sessions_db[session_id] = new_analysis
        print(f"✅ Estrategia lista (Groq): {session_id}")
        
    except Exception as e:
        print(f"❌ Error Groq: {e}")
        sessions_db[session_id] = {"error": f"Error técnico: {str(e)}"}

# --- ENDPOINT 3: RECIBIR DATOS DEL JUEGO ---
@app.post("/update-roster")
async def update_roster(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        session_id = payload.get("session_id")
        team_data = payload.get("team")
        
        # Generamos una ID si el juego no manda una (aunque tu juego debería mandarla)
        if not session_id: 
            import uuid
            session_id = str(uuid.uuid4())[:8]

        # Lanzamos el análisis en segundo plano para responder rápido al juego
        background_tasks.add_task(process_strategy_in_background, session_id, team_data)
        
        # El juego recibe esto y sabe que el proceso comenzó
        return {"status": "queued", "id": session_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- ENDPOINT 4: ENTREGAR RESULTADOS A LA WEB ---
@app.get("/get-analysis")
async def get_analysis(id: str = None):
    if not id: return {"error": "Falta ID"}
    return sessions_db.get(id, {"status": "waiting"})