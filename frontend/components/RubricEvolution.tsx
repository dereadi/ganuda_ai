import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, TextField, Dialog, DialogActions, DialogContent, DialogTitle } from '@mui/material';
import { Rubric, EvolutionData } from '../../types/rubricTypes';

interface RubricEvolutionProps {
  rubric: Rubric;
  onEvolve: (newRubric: Rubric) => void;
}

const RubricEvolution: React.FC<RubricEvolutionProps> = ({ rubric, onEvolve }) => {
  const [open, setOpen] = useState(false);
  const [evolutionData, setEvolutionData] = useState<EvolutionData>({
    criteria: '',
    weight: 0,
    description: ''
  });

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleEvolve = () => {
    const newCriteria = {
      ...rubric.criteria,
      [evolutionData.criteria]: {
        weight: evolutionData.weight,
        description: evolutionData.description
      }
    };
    const newRubric = {
      ...rubric,
      criteria: newCriteria
    };
    onEvolve(newRubric);
    handleClose();
  };

  return (
    <Box>
      <Button variant="contained" color="primary" onClick={handleOpen}>
        Evolve Rubric
      </Button>
      <Dialog open={open} onClose={handleClose}>
        <DialogTitle>Evolve Rubric</DialogTitle>
        <DialogContent>
          <TextField
            label="Criteria"
            value={evolutionData.criteria}
            onChange={(e) => setEvolutionData({ ...evolutionData, criteria: e.target.value })}
            fullWidth
            margin="normal"
          />
          <TextField
            label="Weight"
            type="number"
            value={evolutionData.weight}
            onChange={(e) => setEvolutionData({ ...evolutionData, weight: parseInt(e.target.value, 10) })}
            fullWidth
            margin="normal"
          />
          <TextField
            label="Description"
            value={evolutionData.description}
            onChange={(e) => setEvolutionData({ ...evolutionData, description: e.target.value })}
            fullWidth
            margin="normal"
            multiline
            rows={4}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} color="secondary">
            Cancel
          </Button>
          <Button onClick={handleEvolve} color="primary">
            Evolve
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RubricEvolution;