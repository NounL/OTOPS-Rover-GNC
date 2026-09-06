import './index.css'
import { useEffect, useState } from 'react';
import ControlUI from './pages/ControlUI';
import DataUI from './pages/DataUI';

// Hash routing keeps this dependency-free: #/data is the Data Interface,
// anything else is the Control Interface. Each screen is meant to run on its
// own monitor, so they are separate pages rather than tabs.
function useHashRoute() {
  const [hash, setHash] = useState(window.location.hash);

  useEffect(() => {
    const onHashChange = () => setHash(window.location.hash);
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  return hash;
}

function App() {
  const hash = useHashRoute();

  if (hash.startsWith('#/data')) return <DataUI />;
  return <ControlUI />;
}

export default App;
