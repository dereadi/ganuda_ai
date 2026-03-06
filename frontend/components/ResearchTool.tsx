import React, { useState, useEffect } from 'react';
import { Box, Button, TextField, Typography } from '@mui/material';
import { ResearchToolProps } from '../../types/ResearchToolTypes';

const ResearchTool: React.FC<ResearchToolProps> = ({ onSearch }) => {
  const [query, setQuery] = useState('');

  const handleSearch = () => {
    if (query.trim() !== '') {
      onSearch(query);
    }
  };

  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.key === 'Enter') {
        handleSearch();
      }
    };

    window.addEventListener('keydown', handleKeyPress);

    return () => {
      window.removeEventListener('keydown', handleKeyPress);
    };
  }, [query]);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Research Tool
      </Typography>
      <TextField
        label="Search Query"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        fullWidth
        margin="normal"
      />
      <Button variant="contained" color="primary" onClick={handleSearch}>
        Search
      </Button>
    </Box>
  );
};

export default ResearchTool;