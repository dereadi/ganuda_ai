import React, { useEffect, useState } from 'react';
import { Card, Typography, Spin } from 'antd';
import { FailoverService } from '../../services/failoverService';

const { Title, Text } = Typography;

interface FailoverStatusProps {
  // Define any props if needed
}

const FailoverStatus: React.FC<FailoverStatusProps> = () => {
  const [status, setStatus] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchFailoverStatus = async () => {
      try {
        const status = await FailoverService.getFailoverStatus();
        setStatus(status);
      } catch (error) {
        console.error('Failed to fetch failover status:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchFailoverStatus();
  }, []);

  return (
    <Card title="Failover Status" loading={loading}>
      <Title level={3}>Current Status</Title>
      {loading ? (
        <Spin />
      ) : (
        <Text>{status}</Text>
      )}
    </Card>
  );
};

export default FailoverStatus;