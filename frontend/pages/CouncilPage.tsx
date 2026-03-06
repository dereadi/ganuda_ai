import React, { useEffect, useState } from 'react';
import { OrchestratorComponent } from '../../components/OrchestratorComponent';
import { CouncilService } from '../../services/CouncilService';
import {Council} from '../../models/Council';

const CouncilPage: React.FC = () => {
  const [councils, setCouncils] = useState<Council[]>([]);

  useEffect(() => {
    const fetchCouncils = async () => {
      try {
        const data = await CouncilService.getAllCouncils();
        setCouncils(data);
      } catch (error) {
        console.error('Failed to fetch councils:', error);
      }
    };

    fetchCouncils();
  }, []);

  return (
    <div>
      <h1>Council Page</h1>
      <OrchestratorComponent councils={councils} />
    </div>
  );
};

export default CouncilPage;