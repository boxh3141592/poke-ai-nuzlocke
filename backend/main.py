# main.py (Versión actualizada para google-genai V2)
from fastapi import FastAPI, Request
from google import genai
from google.genai import types
import json
from fastapi.middleware.cors import CORSMiddleware
import os

# --- CONFIGURACIÓN DE SEGURIDAD ---
# Leemos la clave de las variables de entorno (Render)
api_key = os.environ.get("GEMINI_API_KEY")

# Iniciamos el cliente una sola vez
client = genai.Client(api_key=api_key)

app = FastAPI()

# Configuración de CORS para que React pueda hablar con este servidor
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Memoria temporal para guardar el último análisis
latest_analysis = {"status": "waiting", "message": "Esperando datos del juego..."}

@app.post("/update-roster")
async def update_roster(request: Request):
    global latest_analysis
    
    # 1. Recibir datos del juego
    try:
        data = await request.json()
    except Exception:
        return {"status": "error", "message": "JSON inválido recibido"}

    # 2. Preparar el Prompt
    prompt = f"""
    Actúa como el mejor coach competitivo de Pokémon del mundo.
    Estoy jugando un Randomlocke/Nuzlocke difícil.
    
    ESTOS SON MIS RECURSOS:
    1. MI EQUIPO ACTUAL (Party): {data.get('party')}
    2. MI INVENTARIO DE OBJETOS: {data.get('inventory')}
    3. POKÉMON EN EL PC (Reserva): {data.get('box')}

    TU MISIÓN:
    Analiza mi equipo actual para crear la estrategia perfecta.
    
    REGLAS OBLIGATORIAS:
    - **MOVIMIENTOS:** Para cada Pokémon, elige los 4 mejores movimientos ÚNICAMENTE de su lista 'move_pool'. NO inventes movimientos que no estén ahí. La lista 'move_pool' ya incluye lo que pueden recordar y las MTs que tengo en la mochila.
    - **OBJETOS:** Asigna a cada Pokémon el mejor objeto posible que esté en mi lista 'INVENTARIO DE OBJETOS'. Si no tengo nada bueno, di "Sin objeto útil".
    - **ROL:** Define el rol (Sweeper, Wall, Support).
    - **PC:** Si ves un Pokémon en la CAJA (PC) que sea mucho mejor que uno de mi equipo para equilibrar tipos, sugiérelo en el consejo final.

    FORMATO DE RESPUESTA JSON:
    {{
      "analysis_summary": "Tu consejo general. Menciona si debo cambiar a alguien del equipo por alguien del PC y qué objetos equipar.",
      "team": [
        {{
          "species": "Nombre",
          "role": "Rol",
          "item_suggestion": "Objeto de mi inventario",
          "moves": ["Mov1", "Mov2", "Mov3", "Mov4"],
          "ability": "Habilidad",
          "reason": "Breve explicación de por qué este set con estos recursos."
        }}
        ... (para los 6 pokémon)
      ]
    }}
    """

    print("🧠 Enviando datos a Gemini (Nueva Librería)...")
    
    try:
        # 3. Invocar a la API (Sintaxis V2)
        response = client.models.generate_content(
            # Usamos el alias que APARECE en tu captura
            model='gemini-flash-latest',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json'
            )
        )
        
        # Parseamos la respuesta
        latest_analysis = json.loads(response.text)
        print("✅ ¡Análisis completado con éxito!")
        
    except Exception as e:
        print(f"❌ Error con Gemini: {e}")
        latest_analysis = {"error": str(e)}

    return {"status": "success"}

@app.get("/get-analysis")
async def get_analysis():
    return latest_analysis