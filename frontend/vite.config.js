// Configuration du serveur de développement Vite.
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],

  server: {
    // 0.0.0.0 : accessible depuis le réseau local (utile pour tester
    // depuis un autre appareil ou dans un environnement conteneurisé)
    host: '0.0.0.0',
    port: 5173,

    // DEV uniquement : autorise l'hôte de l'aperçu en ligne
    allowedHosts: true,

    // Connexion temps réel (HMR + état des kits) derrière l'aperçu
    // sécurisé : le navigateur doit joindre le WebSocket en wss sur le
    // port 443 de l'hôte public (le proxy le transmet au serveur Vite).
    hmr: {
      protocol: 'wss',
      clientPort: 443,
    },

    // En développement, le navigateur parle UNIQUEMENT au serveur Vite.
    // Vite transmet lui-même les appels commençant par /api au backend
    // FastAPI (port 8000). Le navigateur n'appelle donc jamais
    // directement le backend.
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // WebSocket temps réel (état des kits, puis mesures à l'Étape 8)
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
});
