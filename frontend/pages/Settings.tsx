import React, { useState } from 'react';
import { Box, Button, FormControl, FormLabel, Input, Select, Textarea } from '@chakra-ui/react';
import { useSettings } from '../../hooks/useSettings';

interface SettingsProps {}

const Settings: React.FC<SettingsProps> = () => {
  const [tlsConfig, setTlsConfig] = useState({
    enabled: false,
    certificatePath: '',
    keyPath: '',
    caddyfileContent: ''
  });

  const { saveSettings } = useSettings();

  const handleTlsChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setTlsConfig({ ...tlsConfig, [e.target.name]: e.target.value });
  };

  const saveTlsSettings = () => {
    saveSettings(tlsConfig);
  };

  return (
    <Box p={4}>
      <FormControl>
        <FormLabel>Enable TLS</FormLabel>
        <Input
          type="checkbox"
          name="enabled"
          checked={tlsConfig.enabled}
          onChange={(e) => setTlsConfig({ ...tlsConfig, enabled: e.target.checked })}
        />
      </FormControl>

      <FormControl mt={4} isDisabled={!tlsConfig.enabled}>
        <FormLabel>Certificate Path</FormLabel>
        <Input
          type="text"
          name="certificatePath"
          value={tlsConfig.certificatePath}
          onChange={handleTlsChange}
        />
      </FormControl>

      <FormControl mt={4} isDisabled={!tlsConfig.enabled}>
        <FormLabel>Key Path</FormLabel>
        <Input
          type="text"
          name="keyPath"
          value={tlsConfig.keyPath}
          onChange={handleTlsChange}
        />
      </FormControl>

      <FormControl mt={4} isDisabled={!tlsConfig.enabled}>
        <FormLabel>Caddyfile Content</FormLabel>
        <Textarea
          name="caddyfileContent"
          value={tlsConfig.caddyfileContent}
          onChange={handleTlsChange}
        />
      </FormControl>

      <Button mt={4} colorScheme="blue" onClick={saveTlsSettings}>
        Save Settings
      </Button>
    </Box>
  );
};

export default Settings;