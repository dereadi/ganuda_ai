import React, { useEffect, useState } from 'react';
import { Card, Typography, Grid, CircularProgress } from '@material-ui/core';
import { fetchMoltbookData } from '../../api/MoltbookAPI';

interface MoltbookData {
  id: string;
  name: string;
  status: string;
  lastUpdated: string;
}

const MoltbookMonitor: React.FC = () => {
  const [data, setData] = useState<MoltbookData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const moltbookData = await fetchMoltbookData();
        setData(moltbookData);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch Moltbook data');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <Grid container justify="center" alignItems="center" style={{ height: '100vh' }}>
        <CircularProgress />
      </Grid>
    );
  }

  if (error) {
    return (
      <Grid container justify="center" alignItems="center" style={{ height: '100vh' }}>
        <Typography variant="h5">{error}</Typography>
      </Grid>
    );
  }

  return (
    <Grid container spacing={3} style={{ padding: '20px' }}>
      {data.map((moltbook) => (
        <Grid item xs={12} sm={6} md={4} key={moltbook.id}>
          <Card style={{ padding: '16px', margin: '8px' }}>
            <Typography variant="h6">{moltbook.name}</Typography>
            <Typography variant="body1">Status: {moltbook.status}</Typography>
            <Typography variant="body1">Last Updated: {moltbook.lastUpdated}</Typography>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export default MoltbookMonitor;