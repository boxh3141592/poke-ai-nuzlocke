import { useState, useEffect } from 'react';
import axios from 'axios';

// --- ESTILOS COMPLETOS (Visual bonito) ---
const styles = {
  container: { backgroundColor: '#121212', color: '#e0e0e0', minHeight: '100vh', padding: '20px', fontFamily: 'Segoe UI, sans-serif' },
  header: { textAlign: 'center', color: '#fbbf24', fontSize: '2rem', marginBottom: '20px' },
  summaryBox: { backgroundColor: '#1e1e1e', padding: '20px', borderRadius: '10px', marginBottom: '20px', borderLeft: '5px solid #fbbf24' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' },
  card: { backgroundColor: '#2d2d2d', padding: '15px', borderRadius: '15px', border: '1px solid #333', position: 'relative' },
  clickable: { cursor: 'pointer', transition: 'color 0.2s', textDecoration: 'underline', textDecorationColor: 'rgba(255,255,255,0.2)' },
  pokeName: { color: '#60a5fa', margin: '0', fontSize: '1.4rem', textTransform: 'capitalize', cursor: 'pointer' },
  roleTag: { backgroundColor: '#374151', padding: '2px 8px', borderRadius: '4px', fontSize: '0.8rem', color: '#9ca3af', display: 'inline-block', marginBottom:'10px' },
  moveList: { listStyle: 'none', padding: 0, marginTop: '10px' },
  itemText: { color: '#e0e0e0', position: 'relative', cursor: 'help' }, 
  moveItem: { color: '#34d399', borderBottom: '1px solid #444', padding: '8px 5px', fontSize: '1rem', cursor: 'pointer', position: 'relative', display: 'flex', justifyContent: 'space-between' },
  tooltip: { position: 'absolute', bottom: '110%', left: '50%', transform: 'translateX(-50%)', backgroundColor: '#1f2937', border: '2px solid #fbbf24', borderRadius: '8px', padding: '10px', width: '220px', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)', zIndex: 100, fontSize: '0.85rem', color: '#fff', pointerEvents: 'none', textAlign: 'left' },
  tooltipHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px', borderBottom: '1px solid #444', paddingBottom: '5px' },
  categoryBadge: (cat) => ({ backgroundColor: cat === 'Físico' ? '#dc2626' : (cat === 'Especial' ? '#2563eb' : '#9ca3af'), color: '#fff', padding: '2px 6px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 'bold', textTransform: 'uppercase' })
};

function App() {
  const [data, setData] = useState(null);
  const [hoveredData, setHoveredData] = useState(null);
  const [statusMsg, setStatusMsg] = useState("Cargando...");

  // 1. LÓGICA DE CONEXIÓN (Mantiene la sesión única)
  useEffect(() => {
    const queryParams = new URLSearchParams(window.location.search);
    const sessionId = queryParams.get('id');

    if (!sessionId) {
      setStatusMsg("⚠️ Error: No se detectó ID de sesión. Abre esta página desde el juego.");
      return;
    }

    const fetchData = async () => {
      try {
        // Pedimos datos a Render usando el ID de la URL
        const res = await axios.get(`https://poke-ai-nuzlocke.onrender.com/get-analysis?id=${sessionId}`);
        
        if (res.data.status === 'thinking') {
          setStatusMsg("🧠 La IA está pensando tu estrategia...");
        } else if (res.data.analysis_summary) {
          setData(res.data); // ¡Datos recibidos!
        } else if (res.data.error) {
           setStatusMsg(`❌ Error del servidor: ${res.data.error}`);
        } else {
           setStatusMsg("⏳ Esperando datos del juego...");
        }
      } catch (e) { 
        console.log("Error de red o servidor no listo."); 
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000); // Actualiza cada 3 segundos
    return () => clearInterval(interval);
  }, []);

  // --- FUNCIONES VISUALES (Restauradas) ---
  
  // Obtener GIF animado
  const getGifUrl = (speciesName) => {
    if (!speciesName) return null;
    const cleanName = speciesName.toLowerCase().replace(/ /g, '').replace(/[^a-z0-9]/g, '');
    return `https://play.pokemonshowdown.com/sprites/xyani/${cleanName}.gif`; 
  };

  // Abrir WikiDex
  const openWiki = (term) => {
    if (!term || term === 'Nada' || term === 'Sin objeto útil') return;
    window.open(`https://www.wikidex.net/wiki/${term.split(':')[0].trim().replace(/ /g, '_')}`, '_blank');
  };

  // Buscar detalles del movimiento para el Tooltip
  const getMoveDetails = (pokemonName, moveName) => {
    if (!data?.raw_party_data) return null;
    const rawPokemon = data.raw_party_data.find(p => p.species === pokemonName);
    return rawPokemon?.move_pool?.find(m => m.name.toLowerCase() === moveName.toLowerCase());
  };

  // Buscar descripción del objeto para el Tooltip
  const getItemDescription = (itemName) => {
    if (!data?.inventory_data || !itemName) return "Descripción no disponible.";
    const found = data.inventory_data.find(i => i.toLowerCase().startsWith(itemName.toLowerCase()));
    return found ? (found.includes(':') ? found.split(':').slice(1).join(':').trim() : found) : "Objeto no encontrado.";
  };

  // Si no hay datos, mostrar mensaje de carga
  if (!data) return (
    <div style={{...styles.container, textAlign:'center', display:'flex', flexDirection:'column', justifyContent:'center', alignItems:'center'}}>
      <h1 style={{color: '#fbbf24'}}>🎮 GeminiLink</h1>
      <h3>{statusMsg}</h3>
    </div>
  );

  // RENDERIZADO FINAL (Con todas las funciones visuales)
  return (
    <div style={styles.container}>
      <h1 style={styles.header}>🧠 Estrategia Randomlocke IA (ID: {new URLSearchParams(window.location.search).get('id')})</h1>
      
      {/* Resumen General */}
      {data.analysis_summary && (
        <div style={styles.summaryBox}>
            <strong>💡 Consejo General:</strong>
            <p>{data.analysis_summary}</p>
        </div>
      )}

      {/* Grilla de Pokémon */}
      <div style={styles.grid}>
        {data.team?.map((pkmn, pIndex) => (
          <div key={pIndex} style={styles.card}>
            
            {/* Encabezado: GIF + Nombre Clickeable */}
            <div style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px'}}>
               <img 
                 src={getGifUrl(pkmn.species)} 
                 alt={pkmn.species} 
                 style={{height: '60px', imageRendering: 'pixelated'}} 
                 onError={(e) => { 
                    const staticUrl = `https://img.pokemondb.net/sprites/home/normal/${pkmn.species.toLowerCase()}.png`;
                    if (e.target.src !== staticUrl) e.target.src = staticUrl;
                    else e.target.style.display = 'none';
                 }}
               />
               <h2 style={{...styles.pokeName, ...styles.clickable}} onClick={() => openWiki(pkmn.species)}>{pkmn.species} 🔗</h2>
            </div>

            {/* Rol y Objeto con Tooltip */}
            <span style={styles.roleTag}>{pkmn.role}</span>
            <div style={{marginTop: '5px'}}>
                <strong>Item: </strong>
                <span 
                    style={{...styles.itemText, ...styles.clickable, color: '#fbbf24'}} 
                    onClick={() => openWiki(pkmn.item_suggestion)} 
                    onMouseEnter={() => setHoveredData({ type: 'item', pIndex, content: getItemDescription(pkmn.item_suggestion) })} 
                    onMouseLeave={() => setHoveredData(null)}
                >
                    {pkmn.item_suggestion}
                    {/* Tooltip de Objeto */}
                    {hoveredData?.type === 'item' && hoveredData.pIndex === pIndex && (
                        <div style={styles.tooltip}>
                            <strong>ℹ️ Descripción:</strong>
                            <p style={{marginTop:'5px', color:'#ccc'}}>{hoveredData.content}</p>
                        </div>
                    )}
                </span>
            </div>
            
            {/* Movimientos con Tooltip Técnico */}
            <h4 style={{marginTop:'10px', color:'#fbbf24'}}>Movimientos:</h4>
            <ul style={styles.moveList}>
              {pkmn.moves?.map((moveName, mIndex) => {
                const isHovered = hoveredData?.type === 'move' && hoveredData?.pIndex === pIndex && hoveredData?.mIndex === mIndex;
                const details = isHovered ? getMoveDetails(pkmn.species, moveName) : null;
                
                return (
                  <li key={mIndex} 
                      style={styles.moveItem} 
                      onClick={() => openWiki(moveName)} 
                      onMouseEnter={() => setHoveredData({ type: 'move', pIndex, mIndex })} 
                      onMouseLeave={() => setHoveredData(null)}
                  >
                    <span>⚔️ {moveName}</span><span>🔗</span>
                    
                    {/* Tooltip de Movimiento */}
                    {isHovered && details && (
                        <div style={styles.tooltip}>
                            <div style={styles.tooltipHeader}>
                                <span style={styles.categoryBadge(details.category)}>{details.category}</span>
                                <span style={{fontSize: '0.7em', color: '#bbb'}}>{details.type}</span>
                            </div>
                            <div style={{display:'flex', justifyContent:'space-between', color:'#fbbf24', fontWeight:'bold', marginBottom:'5px'}}>
                                <span>Pow: {details.power > 1 ? details.power : '-'}</span>
                                <span>Acc: {details.accuracy > 0 ? details.accuracy + '%' : '-'}</span>
                            </div>
                            <p style={{fontStyle: 'italic', color: '#ddd', lineHeight: '1.2'}}>{details.desc}</p>
                        </div>
                    )}
                  </li>
                );
              })}
            </ul>
            
            {/* Explicación de la IA */}
            <p style={{marginTop:'10px', fontSize:'0.85em', color:'#888'}}>"{pkmn.reason}"</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;