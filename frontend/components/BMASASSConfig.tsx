import React, { useState } from 'react';
import { Form, Input, Button, Select } from 'antd';
import { BMASASSConfigProps } from '../../types';

const { Option } = Select;

const BMASASSConfig: React.FC<BMASASSConfigProps> = ({ onSubmit }) => {
  const [form] = Form.useForm();

  const handleSubmit = (values: any) => {
    onSubmit(values);
    form.resetFields();
  };

  return (
    <Form form={form} layout="vertical" onFinish={handleSubmit}>
      <Form.Item
        label="API Key"
        name="apiKey"
        rules={[{ required: true, message: 'Please enter your API Key' }]}
      >
        <Input placeholder="Enter your API Key" />
      </Form.Item>
      <Form.Item
        label="Base URL"
        name="baseUrl"
        rules={[{ required: true, message: 'Please enter the Base URL' }]}
      >
        <Input placeholder="Enter the Base URL" />
      </Form.Item>
      <Form.Item
        label="Environment"
        name="environment"
        rules={[{ required: true, message: 'Please select an environment' }]}
      >
        <Select placeholder="Select an environment">
          <Option value="development">Development</Option>
          <Option value="staging">Staging</Option>
          <Option value="production">Production</Option>
        </Select>
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit">
          Save Configuration
        </Button>
      </Form.Item>
    </Form>
  );
};

export default BMASASSConfig;