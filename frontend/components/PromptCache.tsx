import React, { useState, useEffect } from 'react';
import { Prompt, PromptCacheService } from '../../services/PromptCacheService';
import { List, ListItem, Typography, Box } from '@mui/material';

interface PromptCacheProps {
  cacheService: PromptCacheService;
}

const PromptCache: React.FC<PromptCacheProps> = ({ cacheService }) => {
  const [prompts, setPrompts] = useState<Prompt[]>([]);

  useEffect(() => {
    const fetchPrompts = async () => {
      const cachedPrompts = await cacheService.getAllPrompts();
      setPrompts(cachedPrompts);
    };

    fetchPrompts();
  }, [cacheService]);

  return (
    <Box>
      <Typography variant="h5">Cached Prompts</Typography>
      <List>
        {prompts.map((prompt) => (
          <ListItem key={prompt.id}>
            <Typography>{prompt.text}</Typography>
          </ListItem>
        ))}
      </List>
    </Box>
  );
};

export default PromptCache;