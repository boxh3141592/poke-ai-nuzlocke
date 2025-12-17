# main.py (Versión Definitiva - Soporte WikiDex + Tooltips + PBS)
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

    # 2. Preparar el Prompt (ACTUALIZADO PARA DATOS TÉCNICOS/PBS)
    prompt = f"""
    Eres un experto en mecánica de Pokémon, especializado en Nuzlockes de alta dificultad y Fan-Games.
    
    HE EXTRAÍDO LOS DATOS INTERNOS (PBS) DEL JUEGO. 
    **NO ASUMAS NADA POR EL NOMBRE.** Usa los DATOS TÉCNICOS que te envío en el JSON.

    1. MI EQUIPO (Party): {data.get('party')}
       * Nota: Cada movimiento en 'move_pool' incluye ahora su Tipo, Potencia, Precisión y Descripción exacta del juego.
       * Las habilidades y objetos equipados también incluyen su descripción técnica.
    
    2. INVENTARIO DE OBJETOS: {data.get('inventory')}
       * Solo objetos útiles para batalla con sus descripciones.

    3. RESERVA (PC): {data.get('box')}

    TU MISIÓN:
    Diseña la estrategia perfecta basándote en la matemática de los datos enviados (Potencia, Efectos secundarios, Cobertura).
    
    REGLAS OBLIGATORIAS:
    - **DATOS REALES vs CONOCIMIENTO:** Si un movimiento se llama "Golpe Añil" y no lo conoces, ¡LEE SU FICHA! Si dice "Potencia: 100, Tipo: Fuego", úsalo como tal. Lo que yo te envío tiene prioridad sobre tu conocimiento base.
    - **MOVIMIENTOS:** Elige los 4 mejores del 'move_pool' disponible. Prioriza STAB y Cobertura de tipos.
    - **OBJETOS:** Asigna objetos del inventario que sinergicen con la habilidad o los stats del Pokémon (lee las descripciones).
    - **ROLES:** Define si es Atacante Físico, Especial, Muralla, etc., basándote en sus Stats base.

    FORMATO DE RESPUESTA JSON (Exacto para el Frontend):
    {{
      "analysis_summary": "Tu consejo general estratégico. Menciona cambios clave del PC o usos de objetos.",
      "team": [
        {{
          "species": "Nombre",
          "role": "Rol (ej: Sweeper Físico)",
          "item_suggestion": "Nombre del objeto a equipar (del inventario)",
          "moves": ["NombreMov1", "NombreMov2", "NombreMov3", "NombreMov4"],
          "ability": "Nombre Habilidad",
          "reason": "Explica la estrategia basándote en la potencia/efecto de los movimientos elegidos."
        }}
        ... (para los 6 pokémon)
      ]
    }}
    """

    print("🧠 Enviando datos técnicos a Gemini...")
    
    try:
        # 3. Invocar a la API (Modelo Flash Latest)
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json'
            )
        )
        
        # Parseamos la respuesta de la IA
        latest_analysis = json.loads(response.text)
        
        # --- PASO CRÍTICO: INYECTAR DATOS CRUDOS PARA EL FRONTEND ---
        
        # 1. Para Tooltips de Movimientos (Potencia/Precisión)
        if "party" in data:
            latest_analysis["raw_party_data"] = data["party"]
            
        # 2. Para Tooltips de Objetos (Descripción de mochila) - ¡NUEVO!
        if "inventory" in data:
            latest_analysis["inventory_data"] = data["inventory"]
            
        # 3. Para mostrar la Caja del PC
        if "box" in data:
            latest_analysis["box_data"] = data["box"]
            
        print("✅ ¡Análisis completado con éxito!")
        
    except Exception as e:
        print(f"❌ Error con Gemini: {e}")
        latest_analysis = {"error": str(e)}

    return {"status": "success"}

@app.get("/get-analysis")
async def get_analysis():
    return latest_analysis