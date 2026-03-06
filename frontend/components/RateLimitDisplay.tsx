import React, { useState, useEffect } from 'react';
import { RateLimitStatus } from '../../types/RateLimitTypes';
import { fetchRateLimitStatus } from '../../api/RateLimitAPI';

const RateLimitDisplay: React.FC = () => {
  const [rateLimitStatus, setRateLimitStatus] = useState<RateLimitStatus | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const status = await fetchRateLimitStatus();
        setRateLimitStatus(status);
      } catch (error) {
        console.error('Failed to fetch rate limit status:', error);
      }
    };

    fetchStatus();
  }, []);

  if (!rateLimitStatus) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h2>Rate Limit Status</h2>
      <p>Current Limit: {rateLimitStatus.currentLimit}</p>
      <p>Remaining: {rateLimitStatus.remaining}</p>
      <p>Reset Time: {new Date(rateLimitStatus.resetTime).toLocaleString()}</p>
    </div>
  );
};

export default RateLimitDisplay;