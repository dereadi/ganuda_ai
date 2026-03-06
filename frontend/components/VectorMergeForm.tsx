import React, { useState } from 'react';
import { Form, Input, Button, message } from 'antd';
import { VectorMergeService } from '../../services/VectorMergeService';

interface VectorMergeFormProps {
  onMergeComplete: (result: any) => void;
}

const VectorMergeForm: React.FC<VectorMergeFormProps> = ({ onMergeComplete }) => {
  const [loading, setLoading] = useState(false);

  const onFinish = async (values: { vectorA: string, vectorB: string }) => {
    try {
      setLoading(true);
      const result = await VectorMergeService.mergeVectors(values.vectorA, values.vectorB);
      onMergeComplete(result);
      message.success('Vectors merged successfully!');
    } catch (error) {
      message.error('Error merging vectors.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Form layout="vertical" onFinish={onFinish}>
      <Form.Item
        label="Vector A"
        name="vectorA"
        rules={[{ required: true, message: 'Please enter Vector A' }]}
      >
        <Input placeholder="Enter Vector A" />
      </Form.Item>
      <Form.Item
        label="Vector B"
        name="vectorB"
        rules={[{ required: true, message: 'Please enter Vector B' }]}
      >
        <Input placeholder="Enter Vector B" />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading}>
          Merge Vectors
        </Button>
      </Form.Item>
    </Form>
  );
};

export default VectorMergeForm;