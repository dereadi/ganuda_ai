import React, { useEffect, useState } from 'react';
import { Box, Typography, Button } from '@mui/material';
import { TelegramIcon } from '@mui/icons-material';
import { fetchTelegramData } from '../../api/telegramApi';
import { TelegramData } from '../../types/telegramTypes';

const TelegramPage: React.FC = () => {
  const [telegramData, setTelegramData] = useState<TelegramData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await fetchTelegramData();
        setTelegramData(data);
      } catch (err) {
        setError('Failed to fetch Telegram data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <Box>Loading...</Box>;
  }

  if (error) {
    return <Box>Error: {error}</Box>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        <TelegramIcon /> Telegram Updates
      </Typography>
      {telegramData && (
        <Box>
          <Typography variant="h6">Latest Post:</Typography>
          <Typography>{telegramData.latestPost}</Typography>
          <Typography variant="h6">Member Count:</Typography>
          <Typography>{telegramData.memberCount}</Typography>
        </Box>
      )}
      <Button variant="contained" color="primary" href={telegramData?.joinLink}>
        Join Group
      </Button>
    </Box>
  );
};

export default TelegramPage;