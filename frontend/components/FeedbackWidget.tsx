import React, { useState } from 'react';
import { Button, Modal, Form, Input, message } from 'antd';
import { FeedbackService } from '../../services/FeedbackService';

interface FeedbackWidgetProps {
  // Props can be added here if needed
}

const FeedbackWidget: React.FC<FeedbackWidgetProps> = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  const handleOpenModal = () => {
    setIsModalVisible(true);
  };

  const handleCancel = () => {
    setIsModalVisible(false);
    form.resetFields();
  };

  const handleSubmit = async (values: any) => {
    try {
      await FeedbackService.submitFeedback(values);
      message.success('Thank you for your feedback!');
      setIsModalVisible(false);
      form.resetFields();
    } catch (error) {
      message.error('Failed to submit feedback. Please try again later.');
    }
  };

  return (
    <div>
      <Button type="primary" onClick={handleOpenModal}>
        Give Feedback
      </Button>
      <Modal
        title="Provide Feedback"
        visible={isModalVisible}
        onCancel={handleCancel}
        footer={[
          <Button key="back" onClick={handleCancel}>
            Cancel
          </Button>,
          <Button key="submit" type="primary" onClick={() => form.submit()}>
            Submit
          </Button>,
        ]}
      >
        <Form form={form} onFinish={handleSubmit}>
          <Form.Item
            name="name"
            label="Name"
            rules={[{ required: true, message: 'Please enter your name!' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="email"
            label="Email"
            rules={[
              { required: true, message: 'Please enter your email!' },
              { type: 'email', message: 'Please enter a valid email!' },
            ]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="message"
            label="Message"
            rules={[{ required: true, message: 'Please enter your message!' }]}
          >
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default FeedbackWidget;