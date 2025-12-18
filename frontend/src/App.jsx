import { useState, useEffect } from 'react';
import axios from 'axios';

const styles = {
  container: { backgroundColor: '#121212', color: '#e0e0e0', minHeight: '100vh', padding: '20px', fontFamily: 'Segoe UI, sans-serif' },
  card: { backgroundColor: '#2d2d2d', padding: '15px', borderRadius: '15px', border: '1px solid #333', marginBottom: '10px' }
};

function App() {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState("Cargando...");

  useEffect(() => {
    // 1. Leer ID de la URL
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');

    if (!id) {
      setStatus("⚠️ Error: No hay ID de sesión. Abre esto desde el juego.");
      return;
    }

    const fetchData = async () => {
      try {
        // 2. Pedir datos a Render
        const res = await axios.get(`https://poke-ai-nuzlocke.onrender.com/get-analysis?id=${id}`);
        
        if (res.data.status === 'thinking') {
          setStatus("🧠 La IA está pensando...");
        } else if (res.data.status === 'waiting') {
          setStatus("⏳ Esperando datos del juego...");
        } else if (res.data.analysis_summary) {
          setData(res.data);
        }
      } catch (e) { console.error(e); }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  if (!data) return <div style={styles.container}><h1>{status}</h1></div>;

  return (
    <div style={styles.container}>
      <h1 style={{color: '#fbbf24'}}>Estrategia (ID: {new URLSearchParams(window.location.search).get('id')})</h1>
      <div style={{backgroundColor: '#1e1e1e', padding: '20px', borderRadius: '10px', borderLeft: '5px solid #fbbf24'}}>
        <h3>Consejo:</h3>
        <p>{data.analysis_summary}</p>
      </div>

      <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginTop: '20px'}}>
        {data.team?.map((pkmn, i) => (
          <div key={i} style={styles.card}>
            <h2 style={{color: '#60a5fa'}}>{pkmn.species}</h2>
            <p><strong>Rol:</strong> {pkmn.role}</p>
            <p><strong>Objeto:</strong> {pkmn.item_suggestion}</p>
            <ul>{pkmn.moves?.map(m => <li key={m}>{m}</li>)}</ul>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;