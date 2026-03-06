import React, { useEffect, useState } from 'react';
import { Box, Typography, Grid } from '@mui/material';
import MoltbookMonitor from '../../components/MoltbookMonitor';
import FeedbackWidget from '../../components/FeedbackWidget'; // New import

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate data fetching or initialization
    setTimeout(() => {
      setLoading(false);
    }, 2000);
  }, []);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <MoltbookMonitor />
        </Grid>
        <Grid item xs={12} md={6}>
          {/* Additional components can be added here */}
          <FeedbackWidget /> {/* New component */}
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;