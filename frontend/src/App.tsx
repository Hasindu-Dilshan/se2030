import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { RoomCatalog } from './components/RoomCatalog';
import { ManageBookings } from './components/ManageBookings';
import { ShieldCheck, Database, Layers } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'catalog' | 'manage'>('catalog');

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      {/* Top Navigation */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'catalog' ? <RoomCatalog /> : <ManageBookings />}
      </main>

      {/* Footer */}
      <footer className="no-print bg-white border-t border-slate-200 mt-12 py-6 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-800">Tourstay Portal</span>
            <span>—</span>
            <span>SE2030 Software Engineering Academic Project</span>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-400">
            <span className="flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Concurrency Lock Enforced</span>
            </span>
            <span className="flex items-center gap-1">
              <Database className="w-3.5 h-3.5 text-brand-600" />
              <span>SQLAlchemy 2.0 Synchronous</span>
            </span>
            <span className="flex items-center gap-1">
              <Layers className="w-3.5 h-3.5 text-indigo-500" />
              <span>Clean Architecture</span>
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
