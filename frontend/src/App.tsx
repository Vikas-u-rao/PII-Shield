import React from 'react';

export const App: React.FC = () => {
  return (
    <div className="container">
      <header className="header">
        <h1>PIIShield Dashboard</h1>
        <p className="subtitle">
          India-aware, Fail-Closed PII Protection Gateway for LLMs
        </p>
      </header>
      <main className="content">
        <div className="card">
          <h2>System Status</h2>
          <p>Scaffolding initialized. Backend integration coming soon.</p>
        </div>
      </main>
    </div>
  );
};

export default App;
