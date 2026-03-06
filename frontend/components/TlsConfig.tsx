import React, { useState } from 'react';
import { Form, Input, Switch, Button } from 'antd';
import { TlsSettings } from '../../types/TlsSettings';

interface TlsConfigProps {
  initialSettings: TlsSettings;
  onSave: (settings: TlsSettings) => void;
}

const TlsConfig: React.FC<TlsConfigProps> = ({ initialSettings, onSave }) => {
  const [form] = Form.useForm();
  const [tlsSettings, setTlsSettings] = useState<TlsSettings>(initialSettings);

  const handleSave = () => {
    form.validateFields().then((values) => {
      const updatedSettings: TlsSettings = {
        ...tlsSettings,
        ...values,
      };
      setTlsSettings(updatedSettings);
      onSave(updatedSettings);
    });
  };

  return (
    <Form form={form} initialValues={initialSettings}>
      <Form.Item label="Enable TLS" name="enableTls" valuePropName="checked">
        <Switch />
      </Form.Item>
      <Form.Item label="Certificate Path" name="certPath" rules={[{ required: true, message: 'Please enter the certificate path' }]}>
        <Input />
      </Form.Item>
      <Form.Item label="Key Path" name="keyPath" rules={[{ required: true, message: 'Please enter the key path' }]}>
        <Input />
      </Form.Item>
      <Form.Item label="CA Certificate Path" name="caCertPath">
        <Input />
      </Form.Item>
      <Form.Item>
        <Button type="primary" onClick={handleSave}>
          Save
        </Button>
      </Form.Item>
    </Form>
  );
};

export default TlsConfig;