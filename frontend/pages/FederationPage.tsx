import React, { useState, useEffect } from 'react';
import { Box, Button, Typography, TextField } from '@mui/material';
import { useDispatch, useSelector } from 'react-redux';
import { fetchFederations, selectFederations } from '../../store/federationSlice';
import FederationList from '../../components/FederationList';

const FederationPage: React.FC = () => {
  const dispatch = useDispatch();
  const federations = useSelector(selectFederations);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    dispatch(fetchFederations());
  }, [dispatch]);

  const filteredFederations = federations.filter(federation =>
    federation.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Federations
      </Typography>
      <TextField
        label="Search Federations"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        fullWidth
        margin="normal"
      />
      <FederationList federations={filteredFederations} />
      <Button variant="contained" color="primary">
        Add New Federation
      </Button>
    </Box>
  );
};

export default FederationPage;