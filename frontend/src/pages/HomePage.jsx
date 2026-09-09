import { useEffect, useState } from 'react';
import { ActionCard, SectionTitle, EmptyState } from '../components';
import { TestCard } from '../components/TestCard';
import { listRecentTests } from '../services/tests';

export function HomePage({ navigate }) {
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listRecentTests(6)
      .then(setRecent)
      .catch((e) => console.error('Impossible de charger les derniers tests :', e))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <div className="welcome">
        <div>
          <span className="eyebrow accent">CENTRE DE DIAGNOSTIC</span>
          <h2>Bonjour, technicien.</h2>
          <p>Lancez un diagnostic ponctuel (~60 s) et consultez les derniers essais moteurs.</p>
        </div>
        <div className="welcome-icon">⚙</div>
      </div>

      <section className="page-grid two">
        <ActionCard
          icon="✎"
          title="Test manuel"
          text="Saisir manuellement les mesures relevées par le technicien."
          action={() => navigate('motor', { mode: 'manual' })}
          label="Nouveau test manuel"
        />
        <ActionCard
          icon="⌁"
          title="Test automatique"
          text="Connecter le kit ESP32 (PT100 + ADXL345 + SCT-013) pour acquérir automatiquement T°, courant et vibration."
          action={() => navigate('kit')}
          label="Connecter le kit"
        />
      </section>

      <SectionTitle title="Derniers tests" action="Voir l'historique" onAction={() => navigate('history')} />

      {loading ? (
        <div className="empty-state"><span>◌</span><strong>Chargement…</strong></div>
      ) : recent.length === 0 ? (
        <EmptyState
          icon="▤"
          title="Aucun diagnostic enregistré"
          text="Les diagnostics terminés apparaîtront ici."
        />
      ) : (
        <section className="last-tests-grid">
          {recent.map((t) => (
            <TestCard key={t.id} test={t} onOpen={(tt) => navigate('report', { testId: tt.id })} />
          ))}
        </section>
      )}
    </>
  );
}
