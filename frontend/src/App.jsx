import { useState, useEffect } from 'react';
import axios from 'axios';

// Colores para los Tipos
const typeColors = {
  NORMAL: '#A8A77A', FIRE: '#EE8130', WATER: '#6390F0', ELECTRIC: '#F7D02C',
  GRASS: '#7AC74C', ICE: '#96D9D6', FIGHTING: '#C22E28', POISON: '#A33EA1',
  GROUND: '#E2BF65', FLYING: '#A98FF3', PSYCHIC: '#F95587', BUG: '#A6B91A',
  ROCK: '#B6A136', GHOST: '#735797', DRAGON: '#6F35FC', STEEL: '#B7B7CE',
  FAIRY: '#D685AD', DARK: '#705746'
};

const styles = {
  // --- CAMBIO AQUÍ: Estilos del contenedor principal ---
  container: { 
      backgroundColor: '#121212', 
      color: '#e0e0e0', 
      minHeight: '100vh', 
      width: '100%',           // Forzar ancho completo
      boxSizing: 'border-box', // Para que el padding no rompa el ancho
      padding: '20px', 
      margin: 0,               // Quitar márgenes externos
      fontFamily: 'Segoe UI, sans-serif' 
  },
  header: { textAlign: 'center', color: '#fbbf24', fontSize: '2rem', marginBottom: '20px' },
  summaryBox: { backgroundColor: '#1e1e1e', padding: '20px', borderRadius: '10px', marginBottom: '20px', borderLeft: '5px solid #fbbf24' },
  // Grid responsivo: Se adapta al ancho disponible
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', width: '100%' },
  card: { backgroundColor: '#2d2d2d', padding: '15px', borderRadius: '15px', border: '1px solid #333', position: 'relative' },
  clickable: { cursor: 'pointer', transition: 'color 0.2s', textDecoration: 'underline', textDecorationColor: 'rgba(255,255,255,0.2)' },
  pokeName: { color: '#60a5fa', margin: '0', fontSize: '1.4rem', textTransform: 'capitalize', cursor: 'pointer' },
  roleTag: { backgroundColor: '#374151', padding: '2px 8px', borderRadius: '4px', fontSize: '0.8rem', color: '#9ca3af', display: 'inline-block', marginBottom:'10px' },
  moveList: { listStyle: 'none', padding: 0, marginTop: '10px' },
  itemText: { color: '#e0e0e0', position: 'relative', cursor: 'help' }, 
  abilityText: { color: '#a78bfa', position: 'relative', cursor: 'help', fontWeight: 'bold' }, 
  moveItem: { color: '#34d399', borderBottom: '1px solid #444', padding: '8px 5px', fontSize: '1rem', cursor: 'pointer', position: 'relative', display: 'flex', justifyContent: 'space-between' },
  
  tooltip: { 
    position: 'absolute', bottom: '110%', left: '50%', transform: 'translateX(-50%)', 
    backgroundColor: '#1f2937', border: '2px solid #fbbf24', borderRadius: '8px', 
    padding: '10px', width: '220px', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)', 
    zIndex: 100, fontSize: '0.85rem', color: '#fff', pointerEvents: 'none', textAlign: 'left' 
  },
  tooltipHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', borderBottom: '1px solid #444', paddingBottom: '5px' },
  categoryBadge: (cat) => ({ backgroundColor: cat === 'Físico' ? '#dc2626' : (cat === 'Especial' ? '#2563eb' : '#9ca3af'), color: '#fff', padding: '2px 6px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 'bold', textTransform: 'uppercase' }),
  typeBadge: (type) => ({ backgroundColor: typeColors[type?.toUpperCase()] || '#777', color: '#fff', padding: '2px 6px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 'bold', textTransform: 'uppercase' })
};

function App() {
  const [data, setData] = useState(null);
  const [hoveredData, setHoveredData] = useState(null);
  const [statusMsg, setStatusMsg] = useState("Cargando...");

  useEffect(() => {
    const queryParams = new URLSearchParams(window.location.search);
    const sessionId = queryParams.get('id');
    if (!sessionId) { setStatusMsg("⚠️ Error: No se detectó ID de sesión."); return; }

    const fetchData = async () => {
      try {
        const res = await axios.get(`https://poke-ai-nuzlocke.onrender.com/get-analysis?id=${sessionId}`);
        
        if (res.data.status === 'thinking') {
            setStatusMsg("🧠 La IA está pensando...");
        } 
        else if (res.data.analysis_summary) {
            setData(res.data);
        } 
        else if (res.data.error) {
            setStatusMsg(`❌ Error: ${res.data.error}`);
        } 
        else {
            if (!data) {
                setStatusMsg("⏳ Esperando datos del juego...");
            }
        }
      } catch (e) { 
          if (!data) setStatusMsg("Esperando conexión...");
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [data]);

  const getGifUrl = (species) => `https://play.pokemonshowdown.com/sprites/xyani/${species?.toLowerCase().replace(/[^a-z0-9]/g, '')}.gif`;
  const openWiki = (term) => term && window.open(`https://www.wikidex.net/wiki/${term.split(':')[0].trim().replace(/ /g, '_')}`, '_blank');
  
  const getMoveDetails = (pkmnName, moveName) => data?.raw_party_data?.find(p => p.species === pkmnName)?.move_pool?.find(m => m.name.toLowerCase() === moveName.toLowerCase());
  const getItemDescription = (itemName) => {
    const found = data?.inventory_data?.find(i => i.toLowerCase().startsWith(itemName?.toLowerCase()));
    return found ? (found.includes(':') ? found.split(':').slice(1).join(':').trim() : found) : "Descripción no disponible.";
  };

  const getAbilityDescription = (pkmnName, abilityName) => {
    const rawPkmn = data?.raw_party_data?.find(p => p.species === pkmnName);
    if (rawPkmn && rawPkmn.ability && rawPkmn.ability.name === abilityName) {
        return rawPkmn.ability.desc;
    }
    return "Descripción detallada no disponible para sugerencias de caja.";
  };

  if (!data) return <div style={{...styles.container, textAlign:'center', display:'flex', flexDirection:'column', justifyContent:'center', alignItems:'center'}}><h1 style={{color: '#fbbf24'}}>🎮 GeminiLink</h1><h3>{statusMsg}</h3></div>;

  return (
    <div style={styles.container}>
      <h1 style={styles.header}>🧠 Estrategia Randomlocke IA (ID: {new URLSearchParams(window.location.search).get('id')})</h1>
      {data.analysis_summary && <div style={styles.summaryBox}><strong>💡 Consejo:</strong><p>{data.analysis_summary}</p></div>}

      <div style={styles.grid}>
        {data.team?.map((pkmn, pIndex) => (
          <div key={pIndex} style={styles.card}>
            <div style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px'}}>
               <img src={getGifUrl(pkmn.species)} alt={pkmn.species} style={{height: '60px', imageRendering: 'pixelated'}} onError={(e) => { e.target.src = `https://img.pokemondb.net/sprites/home/normal/${pkmn.species.toLowerCase()}.png`; }} />
               <h2 style={{...styles.pokeName, ...styles.clickable}} onClick={() => openWiki(pkmn.species)}>{pkmn.species} 🔗</h2>
            </div>
            <span style={styles.roleTag}>{pkmn.role}</span>

            <div style={{marginTop: '5px'}}>
                <strong>Habilidad: </strong>
                <span 
                    style={{...styles.abilityText, ...styles.clickable}} 
                    onClick={() => openWiki(pkmn.ability)} 
                    onMouseEnter={() => setHoveredData({ type: 'ability', pIndex, content: getAbilityDescription(pkmn.species, pkmn.ability) })} 
                    onMouseLeave={() => setHoveredData(null)}
                >
                    {pkmn.ability}
                    {hoveredData?.type === 'ability' && hoveredData.pIndex === pIndex && (
                        <div style={styles.tooltip}>
                            <strong>ℹ️ Efecto:</strong>
                            <p style={{marginTop:'5px', color:'#ccc'}}>{hoveredData.content}</p>
                        </div>
                    )}
                </span>
            </div>

            <div style={{marginTop: '5px'}}>
                <strong>Item: </strong>
                <span style={{...styles.itemText, ...styles.clickable, color: '#fbbf24'}} onClick={() => openWiki(pkmn.item_suggestion)} onMouseEnter={() => setHoveredData({ type: 'item', pIndex, content: getItemDescription(pkmn.item_suggestion) })} onMouseLeave={() => setHoveredData(null)}>
                    {pkmn.item_suggestion}
                    {hoveredData?.type === 'item' && hoveredData.pIndex === pIndex && (<div style={styles.tooltip}><strong>ℹ️ Descripción:</strong><p style={{marginTop:'5px', color:'#ccc'}}>{hoveredData.content}</p></div>)}
                </span>
            </div>
            
            <h4 style={{marginTop:'10px', color:'#fbbf24'}}>Movimientos:</h4>
            <ul style={styles.moveList}>
              {pkmn.moves?.map((moveName, mIndex) => {
                const isHovered = hoveredData?.type === 'move' && hoveredData?.pIndex === pIndex && hoveredData?.mIndex === mIndex;
                const details = isHovered ? getMoveDetails(pkmn.species, moveName) : null;
                return (
                  <li key={mIndex} style={styles.moveItem} onClick={() => openWiki(moveName)} onMouseEnter={() => setHoveredData({ type: 'move', pIndex, mIndex })} onMouseLeave={() => setHoveredData(null)}>
                    <span>⚔️ {moveName}</span><span>🔗</span>
                    {isHovered && details && (
                        <div style={styles.tooltip}>
                            <div style={styles.tooltipHeader}><span style={styles.categoryBadge(details.category)}>{details.category}</span><span style={styles.typeBadge(details.type)}>{details.type}</span></div>
                            <div style={{display:'flex', justifyContent:'space-between', color:'#fbbf24', fontWeight:'bold', marginBottom:'5px'}}><span>Pow: {details.power > 1 ? details.power : '-'}</span><span>Acc: {details.accuracy > 0 ? details.accuracy + '%' : '-'}</span></div>
                            <p style={{fontStyle: 'italic', color: '#ddd', lineHeight: '1.2'}}>{details.desc}</p>
                        </div>
                    )}
                  </li>
                );
              })}
            </ul>
            <p style={{marginTop:'10px', fontSize:'0.85em', color:'#888'}}>"{pkmn.reason}"</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;