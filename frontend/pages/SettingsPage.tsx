import React, { useState } from 'react';
import { Box, Button, FormControl, FormLabel, Input, Select } from '@chakra-ui/react';
import { useSettings } from '../../hooks/useSettings';

interface SettingsPageProps {
  // Define any props if needed
}

const SettingsPage: React.FC<SettingsPageProps> = () => {
  const [bmasassConfig, setBmasassConfig] = useState({
    enabled: false,
    apiEndpoint: '',
    apiKey: '',
    environment: 'production'
  });

  const { saveSettings } = useSettings();

  const handleSave = () => {
    saveSettings({ bmasass: bmasassConfig });
  };

  return (
    <Box p={4}>
      <FormControl>
        <FormLabel>BMASASS Configuration</FormLabel>
        <Box>
          <FormLabel htmlFor="enabled">Enabled</FormLabel>
          <Input
            id="enabled"
            type="checkbox"
            checked={bmasassConfig.enabled}
            onChange={(e) => setBmasassConfig({ ...bmasassConfig, enabled: e.target.checked })}
          />
        </Box>
        <Box mt={4}>
          <FormLabel htmlFor="apiEndpoint">API Endpoint</FormLabel>
          <Input
            id="apiEndpoint"
            value={bmasassConfig.apiEndpoint}
            onChange={(e) => setBmasassConfig({ ...bmasassConfig, apiEndpoint: e.target.value })}
          />
        </Box>
        <Box mt={4}>
          <FormLabel htmlFor="apiKey">API Key</FormLabel>
          <Input
            id="apiKey"
            value={bmasassConfig.apiKey}
            onChange={(e) => setBmasassConfig({ ...bmasassConfig, apiKey: e.target.value })}
          />
        </Box>
        <Box mt={4}>
          <FormLabel htmlFor="environment">Environment</FormLabel>
          <Select
            id="environment"
            value={bmasassConfig.environment}
            onChange={(e) => setBmasassConfig({ ...bmasassConfig, environment: e.target.value })}
          >
            <option value="production">Production</option>
            <option value="development">Development</option>
          </Select>
        </Box>
        <Button mt={4} onClick={handleSave}>
          Save Settings
        </Button>
      </FormControl>
    </Box>
  );
};

export default SettingsPage;