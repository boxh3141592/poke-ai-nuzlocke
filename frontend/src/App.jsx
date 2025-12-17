import { useState, useEffect } from 'react';
import axios from 'axios';

// --- ESTILOS ---
const styles = {
  container: { backgroundColor: '#121212', color: '#e0e0e0', minHeight: '100vh', padding: '20px', fontFamily: 'Segoe UI, sans-serif' },
  header: { textAlign: 'center', color: '#fbbf24', fontSize: '2rem', marginBottom: '20px' },
  summaryBox: { backgroundColor: '#1e1e1e', padding: '20px', borderRadius: '10px', marginBottom: '20px', borderLeft: '5px solid #fbbf24' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' },
  card: { backgroundColor: '#2d2d2d', padding: '15px', borderRadius: '15px', border: '1px solid #333', position: 'relative' },
  pokeName: { color: '#60a5fa', margin: '0 0 5px 0', fontSize: '1.4rem', textTransform: 'capitalize' },
  roleTag: { backgroundColor: '#374151', padding: '2px 8px', borderRadius: '4px', fontSize: '0.8rem', color: '#9ca3af', display: 'inline-block', marginBottom:'10px' },
  moveList: { listStyle: 'none', padding: 0, marginTop: '10px' },
  
  // Estilo del Movimiento (Item)
  moveItem: { 
    color: '#34d399', 
    borderBottom: '1px solid #444', 
    padding: '8px 5px', 
    fontSize: '1rem', 
    cursor: 'help', // Cambia el cursor para indicar que se puede interactuar
    position: 'relative',
    transition: 'background 0.2s'
  },

  // --- EL TOOLTIP (LA TARJETA FLOTANTE) ---
  tooltip: {
    position: 'absolute',
    bottom: '120%', // Aparece encima del texto
    left: '50%',
    transform: 'translateX(-50%)',
    backgroundColor: '#1f2937', // Fondo oscuro azulado
    border: '2px solid #fbbf24', // Borde dorado como tu referencia
    borderRadius: '8px',
    padding: '10px',
    width: '220px',
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)',
    zIndex: 100,
    fontSize: '0.85rem',
    color: '#fff',
    pointerEvents: 'none' // Para que no titile
  },
  tooltipHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
    borderBottom: '1px solid #444',
    paddingBottom: '5px'
  },
  categoryBadge: (cat) => ({
    backgroundColor: cat === 'Físico' ? '#dc2626' : (cat === 'Especial' ? '#2563eb' : '#9ca3af'),
    color: '#fff',
    padding: '2px 6px',
    borderRadius: '4px',
    fontSize: '0.7rem',
    fontWeight: 'bold',
    textTransform: 'uppercase'
  }),
  tooltipStats: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '8px',
    fontWeight: 'bold',
    color: '#fbbf24'
  }
};

function App() {
  const [data, setData] = useState(null);
  const [hoveredMove, setHoveredMove] = useState(null); // Guardamos qué ataque se está mirando

  useEffect(() => {
    const fetchData = async () => {
      try {
        // RECUERDA: Cambia esta URL por la de tu Render si ya lo subiste
        const res = await axios.get('https://poke-ai-nuzlocke.onrender.com/get-analysis');
        if (res.data && res.data.analysis_summary) setData(res.data);
      } catch (e) { console.log("Esperando datos..."); }
    };
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  // --- LÓGICA DE BÚSQUEDA DE DATOS ---
  // Busca los detalles técnicos del ataque en la data cruda que vino de Ruby
  const getMoveDetails = (pokemonName, moveName) => {
    if (!data || !data.raw_party_data) return null;
    
    // 1. Encontrar al Pokémon correcto en la data cruda
    const rawPokemon = data.raw_party_data.find(p => p.species === pokemonName);
    if (!rawPokemon || !rawPokemon.move_pool) return null;

    // 2. Buscar el ataque dentro de su move_pool (comparamos nombres ignorando mayúsculas)
    const moveDetails = rawPokemon.move_pool.find(m => m.name.toLowerCase() === moveName.toLowerCase());
    
    return moveDetails; 
  };

  if (!data) return <div style={{...styles.container, textAlign:'center'}}><h1>🎮 Esperando datos del juego...</h1></div>;

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
            <h2 style={styles.pokeName}>{pkmn.species}</h2>
            <span style={styles.roleTag}>{pkmn.role}</span>
            <p><strong>Item:</strong> {pkmn.item_suggestion}</p>
            
            <h4 style={{marginTop:'10px', color:'#fbbf24'}}>Movimientos Recomendados:</h4>
            <ul style={styles.moveList}>
              {pkmn.moves?.map((moveName, mIndex) => {
                
                // Verificamos si este es el ataque que el mouse está tocando
                const isHovered = hoveredMove?.pIndex === pIndex && hoveredMove?.mIndex === mIndex;
                const details = isHovered ? getMoveDetails(pkmn.species, moveName) : null;

                return (
                  <li 
                    key={mIndex} 
                    style={styles.moveItem}
                    onMouseEnter={() => setHoveredMove({ pIndex, mIndex })}
                    onMouseLeave={() => setHoveredMove(null)}
                  >
                    ⚔️ {moveName}

                    {/* --- AQUÍ ESTÁ EL POP-UP --- */}
                    {isHovered && details && (
                      <div style={styles.tooltip}>
                        <div style={styles.tooltipHeader}>
                           {/* Icono de Categoría (Simulado con color) */}
                           <span style={styles.categoryBadge(details.category)}>{details.category}</span>
                           <span style={{fontSize: '0.7em', color: '#bbb'}}>{details.type}</span>
                        </div>
                        
                        <div style={styles.tooltipStats}>
                          <span>Poder: {details.power > 1 ? details.power : '-'}</span>
                          <span>Prec: {details.accuracy > 0 ? details.accuracy + '%' : '-'}</span>
                        </div>
                        
                        <p style={{fontStyle: 'italic', color: '#ddd', lineHeight: '1.2'}}>
                          {details.desc}
                        </p>
                      </div>
                    )}
                    {/* --------------------------- */}
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