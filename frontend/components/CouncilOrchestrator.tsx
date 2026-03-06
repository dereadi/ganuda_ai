import React, { useState, useEffect } from 'react';
import {Council} from '../../models/Council';
import CouncilList from './CouncilList';
import CouncilForm from './CouncilForm';

interface CouncilOrchestratorProps {
  councils: Council[];
  onCouncilAdd: (council: Council) => void;
  onCouncilUpdate: (council: Council) => void;
  onCouncilDelete: (councilId: string) => void;
}

const CouncilOrchestrator: React.FC<CouncilOrchestratorProps> = ({ councils, onCouncilAdd, onCouncilUpdate, onCouncilDelete }) => {
  const [showForm, setShowForm] = useState(false);

  const handleFormClose = () => {
    setShowForm(false);
  };

  const handleCouncilAdd = (council: Council) => {
    onCouncilAdd(council);
    setShowForm(false);
  };

  const handleCouncilUpdate = (council: Council) => {
    onCouncilUpdate(council);
    setShowForm(false);
  };

  return (
    <div className="council-orchestrator">
      <h2>Council Orchestrator</h2>
      <button onClick={() => setShowForm(true)}>Add New Council</button>
      {showForm && (
        <CouncilForm
          onClose={handleFormClose}
          onCouncilAdd={handleCouncilAdd}
          onCouncilUpdate={handleCouncilUpdate}
        />
      )}
      <CouncilList
        councils={councils}
        onCouncilDelete={onCouncilDelete}
        onCouncilEdit={(council) => {
          setShowForm(true);
        }}
      />
    </div>
  );
};

export default CouncilOrchestrator;