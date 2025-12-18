import { useState, useEffect } from 'react';
import axios from 'axios';

const styles = {
  container: { backgroundColor: '#121212', color: '#e0e0e0', minHeight: '100vh', padding: '20px', fontFamily: 'Segoe UI, sans-serif' },
  header: { textAlign: 'center', color: '#fbbf24', fontSize: '2rem', marginBottom: '20px' },
  summaryBox: { backgroundColor: '#1e1e1e', padding: '20px', borderRadius: '10px', marginBottom: '20px', borderLeft: '5px solid #fbbf24' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' },
  card: { backgroundColor: '#2d2d2d', padding: '15px', borderRadius: '15px', border: '1px solid #333', position: 'relative' },
  
  // Estilos interactivos
  clickable: { cursor: 'pointer', transition: 'color 0.2s', textDecoration: 'underline', textDecorationColor: 'rgba(255,255,255,0.2)' },
  pokeName: { color: '#60a5fa', margin: '0', fontSize: '1.4rem', textTransform: 'capitalize', cursor: 'pointer' },
  
  roleTag: { backgroundColor: '#374151', padding: '2px 8px', borderRadius: '4px', fontSize: '0.8rem', color: '#9ca3af', display: 'inline-block', marginBottom:'10px' },
  moveList: { listStyle: 'none', padding: 0, marginTop: '10px' },
  
  itemText: { color: '#e0e0e0', position: 'relative', cursor: 'help' }, 
  moveItem: { 
    color: '#34d399', borderBottom: '1px solid #444', padding: '8px 5px', fontSize: '1rem', 
    cursor: 'pointer', position: 'relative', display: 'flex', justifyContent: 'space-between' 
  },

  // Tooltip Flotante
  tooltip: {
    position: 'absolute', bottom: '110%', left: '50%', transform: 'translateX(-50%)',
    backgroundColor: '#1f2937', border: '2px solid #fbbf24', borderRadius: '8px', padding: '10px',
    width: '220px', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)', zIndex: 100, fontSize: '0.85rem', color: '#fff', pointerEvents: 'none', textAlign: 'left'
  },
  tooltipHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px', borderBottom: '1px solid #444', paddingBottom: '5px' },
  categoryBadge: (cat) => ({
    backgroundColor: cat === 'Físico' ? '#dc2626' : (cat === 'Especial' ? '#2563eb' : '#9ca3af'),
    color: '#fff', padding: '2px 6px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 'bold', textTransform: 'uppercase'
  })
};

function App() {
  const [data, setData] = useState(null);
  const [hoveredData, setHoveredData] = useState(null); 

  useEffect(() => {
    const fetchData = async () => {
      try {
        // URL DE RENDER
        const res = await axios.get('https://poke-ai-nuzlocke.onrender.com/get-analysis');
        if (res.data && res.data.analysis_summary) setData(res.data);
      } catch (e) { console.log("Esperando datos..."); }
    };
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  // --- FUNCIÓN PARA OBTENER URL DEL ICONO ---
  const getIconUrl = (fileName) => {
    if (!fileName) return null;
    // Forzamos MAYÚSCULAS para que coincida con tus archivos (ej: "QUILAVA.png")
    const cleanName = String(fileName).toUpperCase();
    return `/pokemon-icons/${cleanName}.png`; 
  };

  const openWiki = (term) => {
    if (!term || term === 'Nada' || term === 'Sin objeto útil') return;
    const cleanTerm = term.split(':')[0].trim().replace(/ /g, '_'); 
    window.open(`https://www.wikidex.net/wiki/${cleanTerm}`, '_blank');
  };

  const getMoveDetails = (pokemonName, moveName) => {
    if (!data?.raw_party_data) return null;
    const rawPokemon = data.raw_party_data.find(p => p.species === pokemonName);
    return rawPokemon?.move_pool?.find(m => m.name.toLowerCase() === moveName.toLowerCase());
  };

  const getItemDescription = (itemName) => {
    if (!data?.inventory_data || !itemName) return "Descripción no disponible en mochila.";
    const found = data.inventory_data.find(i => i.toLowerCase().startsWith(itemName.toLowerCase()));
    if (found) {
        return found.includes(':') ? found.split(':').slice(1).join(':').trim() : found;
    }
    return "Objeto no encontrado en inventario.";
  };

  if (!data) return <div style={{...styles.container, textAlign:'center'}}><h1>🎮 Esperando datos...</h1></div>;

  return (
    <div style={styles.container}>
      <h1 style={styles.header}>🧠 Estrategia Randomlocke IA</h1>
      
      {data.analysis_summary && (
        <div style={styles.summaryBox}>
          <strong>💡 Consejo General:</strong>
          <p>{data.analysis_summary}</p>
        </div>
      )}

      <div style={styles.grid}>
        {data.team?.map((pkmn, pIndex) => (
          <div key={pIndex} style={styles.card}>
            
            {/* --- CABECERA (ICONO + NOMBRE) --- */}
            <div style={{display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px'}}>
               
               {/* 🖼️ ICONO CON SISTEMA DE RESPALDO (SMART FALLBACK) 🖼️ */}
               <img 
                 src={getIconUrl(pkmn.icon_file)} 
                 alt={pkmn.species} 
                 style={{width: '64px', height: '64px', imageRendering: 'pixelated'}} 
                 onError={(e) => { 
                    // Si falla la carga (ej: no existe QUILAVA_1.png), entra aquí.
                    
                    // 1. Calculamos el nombre base usando la Especie (ej: QUILAVA)
                    const baseName = String(pkmn.species).toUpperCase();
                    const backupUrl = `/pokemon-icons/${baseName}.png`;
                    
                    // 2. Verificamos para no entrar en bucle infinito
                    // Si la imagen que falló NO es la de respaldo, intentamos cargar el respaldo.
                    if (!e.target.src.toUpperCase().endsWith(backupUrl.toUpperCase())) {
                        console.log(`⚠️ Icono exacto no encontrado para ${pkmn.species}, probando base: ${baseName}`);
                        e.target.src = backupUrl; 
                    } else {
                        // 3. Si el respaldo también falla, ocultamos la imagen
                        e.target.style.display = 'none';
                    }
                 }}
               />
               
               {/* NOMBRE (CLICKABLE) */}
               <h2 
                 style={{...styles.pokeName, ...styles.clickable}} 
                 onClick={() => openWiki(pkmn.species)}
                 title="Ver en WikiDex"
               >
                 {pkmn.species} 🔗
               </h2>
            </div>

            <span style={styles.roleTag}>{pkmn.role}</span>
            
            {/* OBJETO (HOVER + CLICKABLE) */}
            <div style={{marginTop: '5px'}}>
                <strong>Item: </strong>
                <span 
                    style={{...styles.itemText, ...styles.clickable, color: '#fbbf24'}}
                    onClick={() => openWiki(pkmn.item_suggestion)}
                    onMouseEnter={() => setHoveredData({ type: 'item', pIndex, content: getItemDescription(pkmn.item_suggestion) })}
                    onMouseLeave={() => setHoveredData(null)}
                >
                    {pkmn.item_suggestion}
                    
                    {hoveredData?.type === 'item' && hoveredData.pIndex === pIndex && (
                        <div style={styles.tooltip}>
                            <strong>ℹ️ Descripción:</strong>
                            <p style={{marginTop:'5px', color:'#ccc'}}>{hoveredData.content}</p>
                            <p style={{fontSize:'0.7em', color:'#60a5fa', marginTop:'5px'}}>(Click para ver en WikiDex)</p>
                        </div>
                    )}
                </span>
            </div>
            
            <h4 style={{marginTop:'10px', color:'#fbbf24'}}>Movimientos:</h4>
            <ul style={styles.moveList}>
              {pkmn.moves?.map((moveName, mIndex) => {
                const isHovered = hoveredData?.type === 'move' && hoveredData?.pIndex === pIndex && hoveredData?.mIndex === mIndex;
                const details = isHovered ? getMoveDetails(pkmn.species, moveName) : null;

                return (
                  <li 
                    key={mIndex} 
                    style={styles.moveItem}
                    onClick={() => openWiki(moveName)}
                    onMouseEnter={() => setHoveredData({ type: 'move', pIndex, mIndex })}
                    onMouseLeave={() => setHoveredData(null)}
                  >
                    <span>⚔️ {moveName}</span>
                    <span style={{fontSize:'0.8em', color:'#666'}}>🔗</span>

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
                        <p style={{fontStyle: 'italic', color: '#ddd', lineHeight: '1.2'}}>
                          {details.desc}
                        </p>
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