# main.py (Versión Turbo - Background Tasks)
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

# Memoria temporal
latest_analysis = {"status": "waiting", "message": "Esperando datos..."}

# --- FUNCIÓN QUE CORRE EN SEGUNDO PLANO (LA IA PENSANDO) ---
def process_strategy_in_background(data: dict):
    global latest_analysis
    print("🧠 Gemini ha empezado a pensar en segundo plano...")
    
    # Preparamos el Prompt (Tu versión completa)
    prompt = f"""
    Eres un experto en mecánica de Pokémon (Nuzlockes/Fan-Games).
    HE EXTRAÍDO LOS DATOS INTERNOS (PBS) DEL JUEGO.
    
    1. EQUIPO (Party): {data.get('party')}
    2. INVENTARIO: {data.get('inventory')}
    3. RESERVA (PC): {data.get('box')}

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
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type='application/json')
        )
        
        # Guardamos el resultado de la IA
        new_analysis = json.loads(response.text)
        
        # Inyectamos los datos crudos para los Tooltips del Frontend
        if "party" in data: new_analysis["raw_party_data"] = data["party"]
        if "inventory" in data: new_analysis["inventory_data"] = data["inventory"]
        if "box" in data: new_analysis["box_data"] = data["box"]
            
        latest_analysis = new_analysis
        print("✅ ¡Estrategia lista y guardada en memoria!")
        
    except Exception as e:
        print(f"❌ Error en segundo plano: {e}")
        latest_analysis = {"error": str(e)}

# --- EL ENDPOINT RÁPIDO ---
@app.post("/update-roster")
async def update_roster(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        
        # AQUÍ ESTÁ EL TRUCO:
        # En vez de esperar, le decimos a FastAPI: "Ejecuta esto después de responder"
        background_tasks.add_task(process_strategy_in_background, data)
        
        # Respondemos al juego INMEDIATAMENTE
        return {"status": "queued", "message": "Datos recibidos, procesando..."}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/get-analysis")
async def get_analysis():
    return latest_analysis