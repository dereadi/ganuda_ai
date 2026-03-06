import React, { useState } from 'react';
import { Button, Input, Typography } from 'antd';
import { VectorService } from '../../services/VectorService';
import { Vector } from '../../models/Vector';

const { Title } = Typography;

interface VectorMergingPageProps {
  // Define any props if needed
}

const VectorMergingPage: React.FC<VectorMergingPageProps> = () => {
  const [vectorA, setVectorA] = useState<string>('');
  const [vectorB, setVectorB] = useState<string>('');
  const [mergedVector, setMergedVector] = useState<string>('');
  const [error, setError] = useState<string>('');

  const handleMergeVectors = async () => {
    try {
      const parsedVectorA = JSON.parse(vectorA);
      const parsedVectorB = JSON.parse(vectorB);

      const result = await VectorService.mergeVectors(parsedVectorA, parsedVectorB);
      setMergedVector(JSON.stringify(result));
      setError('');
    } catch (err) {
      setError('Error merging vectors. Please check your input.');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <Title level={2}>Vector Merging</Title>
      <div>
        <Input
          placeholder="Enter vector A (JSON format)"
          value={vectorA}
          onChange={(e) => setVectorA(e.target.value)}
          style={{ width: '100%', marginBottom: '10px' }}
        />
        <Input
          placeholder="Enter vector B (JSON format)"
          value={vectorB}
          onChange={(e) => setVectorB(e.target.value)}
          style={{ width: '100%', marginBottom: '10px' }}
        />
        <Button type="primary" onClick={handleMergeVectors}>
          Merge Vectors
        </Button>
      </div>
      {mergedVector && (
        <div style={{ marginTop: '20px' }}>
          <Title level={3}>Merged Vector</Title>
          <pre>{mergedVector}</pre>
        </div>
      )}
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
};

export default VectorMergingPage;