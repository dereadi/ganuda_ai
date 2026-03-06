import React, { useState } from 'react';
import { Button, Input, Modal, Form } from 'antd';
import { FederatedService } from '../../services/FederatedService';
import { IFederationExtensionProps } from './types';

const FederationExtension: React.FC<IFederationExtensionProps> = ({ onFederationSuccess }) => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      await FederatedService.extendFederation(values);
      onFederationSuccess();
      setIsModalVisible(false);
    } catch (error) {
      console.error('Error extending federation:', error);
    }
  };

  const handleCancel = () => {
    setIsModalVisible(false);
  };

  return (
    <div>
      <Button type="primary" onClick={() => setIsModalVisible(true)}>
        Extend Federation
      </Button>
      <Modal
        title="Extend Federation"
        visible={isModalVisible}
        onOk={handleOk}
        onCancel={handleCancel}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="Federation ID"
            name="federationId"
            rules={[{ required: true, message: 'Please enter the Federation ID' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            label="New Member"
            name="newMember"
            rules={[{ required: true, message: 'Please enter the new member details' }]}
          >
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default FederationExtension;