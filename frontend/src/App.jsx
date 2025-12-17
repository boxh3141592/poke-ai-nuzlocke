import { useState, useEffect } from 'react';
import axios from 'axios';

const styles = {
  container: { backgroundColor: '#121212', color: '#e0e0e0', minHeight: '100vh', padding: '20px', fontFamily: 'Segoe UI, sans-serif' },
  header: { textAlign: 'center', color: '#fbbf24', fontSize: '2rem', marginBottom: '20px' },
  summaryBox: { backgroundColor: '#1e1e1e', padding: '20px', borderRadius: '10px', marginBottom: '20px', borderLeft: '5px solid #fbbf24' },
  tabContainer: { display: 'flex', justifyContent: 'center', marginBottom: '20px', gap: '10px' },
  tabButton: (isActive) => ({
    padding: '10px 20px', cursor: 'pointer', borderRadius: '5px', border: 'none', fontWeight: 'bold',
    backgroundColor: isActive ? '#fbbf24' : '#333', color: isActive ? '#000' : '#fff', transition: '0.3s'
  }),
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' },
  card: { backgroundColor: '#2d2d2d', padding: '15px', borderRadius: '15px', border: '1px solid #333', position: 'relative' },
  pokeName: { color: '#60a5fa', margin: '0 0 5px 0', fontSize: '1.4rem', textTransform: 'capitalize' },
  subText: { fontSize: '0.9rem', color: '#aaa', margin: '2px 0' },
  moveList: { listStyle: 'none', padding: 0, marginTop: '10px' },
  moveItem: { color: '#34d399', borderBottom: '1px solid #444', padding: '4px 0', fontSize: '0.95rem' },
  pcTag: { position: 'absolute', top: '10px', right: '10px', background: '#555', padding: '2px 6px', borderRadius: '4px', fontSize: '0.7rem' }
};

function App() {
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState('team'); // 'team' o 'pc'

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get('http://127.0.0.1:8000/get-analysis');
        if (res.data && res.data.analysis_summary) setData(res.data);
      } catch (e) { console.log("Esperando..."); }
    };
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  if (!data) return <div style={{...styles.container, textAlign:'center'}}><h1>🎮 Esperando datos del NPC...</h1></div>;

  // Renderizar una tarjeta de Pokémon
  const renderCard = (pkmn, isPC = false) => (
    <div key={Math.random()} style={styles.card}>
      <h2 style={styles.pokeName}>{pkmn.species} {isPC && <span style={{fontSize:'0.6em'}}>Lvl {pkmn.level}</span>}</h2>
      {!isPC && <span style={{background:'#374151', padding:'3px 8px', borderRadius:'4px', fontSize:'0.8rem'}}>{pkmn.role}</span>}
      
      <div style={{marginTop: '10px'}}>
        <p style={styles.subText}><strong>Hab:</strong> {pkmn.ability}</p>
        <p style={styles.subText}><strong>Item:</strong> {isPC ? (pkmn.held_item || "Nada") : pkmn.item_suggestion}</p>
      </div>

      {!isPC && (
        <>
          <h4 style={{marginTop:'10px', color:'#fbbf24', fontSize:'1rem'}}>Estrategia:</h4>
          <ul style={styles.moveList}>
            {pkmn.moves?.map((m, i) => <li key={i} style={styles.moveItem}>⚔️ {m}</li>)}
          </ul>
          <p style={{marginTop:'10px', fontSize:'0.85em', fontStyle:'italic', color:'#888'}}>"{pkmn.reason}"</p>
        </>
      )}
       
      {isPC && ( // Info simplificada para PC
        <div style={{marginTop:'10px'}}>
             <p style={styles.subText}>Tipos: {pkmn.types?.join("/")}</p>
             <p style={{marginTop:'5px', color:'#888', fontSize:'0.8em'}}>Movimientos actuales: {pkmn.current_moves?.slice(0,4).join(", ")}</p>
        </div>
      )}
    </div>
  );

  return (
    <div style={styles.container}>
      <h1 style={styles.header}>🧠 Pokémon AI Coach</h1>
      
      {data.analysis_summary && (
        <div style={styles.summaryBox}>
          <strong>💡 Consejo General:</strong>
          <p style={{marginTop: '5px'}}>{data.analysis_summary}</p>
        </div>
      )}

      {/* Pestañas de Navegación */}
      <div style={styles.tabContainer}>
        <button style={styles.tabButton(activeTab === 'team')} onClick={() => setActiveTab('team')}>
          ⚔️ Mi Equipo Activo
        </button>
        <button style={styles.tabButton(activeTab === 'pc')} onClick={() => setActiveTab('pc')}>
          📦 Caja de PC ({data.box_data ? data.box_data.length : 'Ver PC'})
        </button>
      </div>
      
      {/* Contenido según pestaña */}
      <div style={styles.grid}>
        {activeTab === 'team' && data.team?.map(p => renderCard(p, false))}
        
        {/* Si estamos en PC, mostramos los datos crudos del PC si la IA no los procesó, o leemos directo del json raw si lo pasamos */}
        {activeTab === 'pc' && (
            // Nota: Para ver el PC, necesitamos que el backend nos pase la data "raw" de la caja también.
            // Si la IA no devolvió la lista del PC en su respuesta JSON, la web no la verá.
            // Muestro un mensaje si no hay datos de PC procesados.
            <div style={{gridColumn: '1/-1', textAlign: 'center', color: '#888'}}>
                <p>La IA analizó el PC para darte el consejo, pero para ver la lista completa aquí, <br/>necesitamos pedirle que devuelva la lista de la caja también (consume más tokens).</p>
                <p><em>Lee el "Consejo General" arriba para ver a quién te recomienda sacar del PC.</em></p>
            </div>
        )}
      </div>
    </div>
  );
}

export default App;