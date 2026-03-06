import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { HardwareItem } from '../../types/HardwareTypes';

const { confirm } = Modal;

interface HardwareInventoryProps {
  hardwareItems: HardwareItem[];
  onAddHardware: (hardware: HardwareItem) => void;
  onUpdateHardware: (hardware: HardwareItem) => void;
  onDeleteHardware: (id: string) => void;
}

const HardwareInventory: React.FC<HardwareInventoryProps> = ({ hardwareItems, onAddHardware, onUpdateHardware, onDeleteHardware }) => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [editingItem, setEditingItem] = useState<HardwareItem | null>(null);

  const columns: ColumnsType<HardwareItem> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: 'Serial Number',
      dataIndex: 'serialNumber',
      key: 'serialNumber',
    },
    {
      title: 'Location',
      dataIndex: 'location',
      key: 'location',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <div>
          <Button type="link" onClick={() => handleEdit(record)}>
            Edit
          </Button>
          <Button type="link" onClick={() => handleDelete(record.id)}>
            Delete
          </Button>
        </div>
      ),
    },
  ];

  const handleAdd = () => {
    form.resetFields();
    setEditingItem(null);
    setIsModalVisible(true);
  };

  const handleEdit = (item: HardwareItem) => {
    form.setFieldsValue(item);
    setEditingItem(item);
    setIsModalVisible(true);
  };

  const handleDelete = (id: string) => {
    confirm({
      title: 'Are you sure you want to delete this item?',
      okText: 'Yes',
      okType: 'danger',
      cancelText: 'No',
      onOk() {
        onDeleteHardware(id);
      },
    });
  };

  const handleModalOk = () => {
    form.validateFields().then((values) => {
      if (editingItem) {
        onUpdateHardware({ ...editingItem, ...values });
      } else {
        onAddHardware(values as HardwareItem);
      }
      setIsModalVisible(false);
    });
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
  };

  return (
    <div>
      <Button type="primary" onClick={handleAdd}>
        Add Hardware
      </Button>
      <Table dataSource={hardwareItems} columns={columns} rowKey="id" />
      <Modal
        title={editingItem ? 'Edit Hardware' : 'Add Hardware'}
        visible={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
      >
        <Form form={form} layout="vertical">
          <Form.Item label="Name" name="name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="Type" name="type" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="Serial Number" name="serialNumber" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="Location" name="location" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default HardwareInventory;