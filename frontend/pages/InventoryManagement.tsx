import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { InventoryService } from '../../services/InventoryService';
import { HardwareItem } from '../../models/HardwareItem';

const { confirm } = Modal;

interface InventoryManagementProps {
  // Define any props if needed
}

const InventoryManagement: React.FC<InventoryManagementProps> = () => {
  const [hardwareItems, setHardwareItems] = useState<HardwareItem[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchHardwareItems();
  }, []);

  const fetchHardwareItems = async () => {
    try {
      const items = await InventoryService.getHardwareItems();
      setHardwareItems(items);
    } catch (error) {
      console.error('Failed to fetch hardware items:', error);
    }
  };

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
      title: 'Quantity',
      dataIndex: 'quantity',
      key: 'quantity',
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
          <Button type="link" onClick={() => showEditModal(record)}>
            Edit
          </Button>
          <Button type="link" danger onClick={() => showDeleteConfirm(record.id)}>
            Delete
          </Button>
        </div>
      ),
    },
  ];

  const showEditModal = (item: HardwareItem) => {
    form.setFieldsValue(item);
    setIsModalVisible(true);
  };

  const showDeleteConfirm = (id: string) => {
    confirm({
      title: 'Are you sure you want to delete this item?',
      okText: 'Yes',
      okType: 'danger',
      cancelText: 'No',
      onOk() {
        deleteHardwareItem(id);
      },
    });
  };

  const deleteHardwareItem = async (id: string) => {
    try {
      await InventoryService.deleteHardwareItem(id);
      fetchHardwareItems();
    } catch (error) {
      console.error('Failed to delete hardware item:', error);
    }
  };

  const handleAdd = async (values: HardwareItem) => {
    try {
      await InventoryService.addHardwareItem(values);
      fetchHardwareItems();
      form.resetFields();
      setIsModalVisible(false);
    } catch (error) {
      console.error('Failed to add hardware item:', error);
    }
  };

  const handleEdit = async (values: HardwareItem) => {
    try {
      await InventoryService.updateHardwareItem(values);
      fetchHardwareItems();
      form.resetFields();
      setIsModalVisible(false);
    } catch (error) {
      console.error('Failed to update hardware item:', error);
    }
  };

  return (
    <div>
      <h1>Inventory Management</h1>
      <Button type="primary" onClick={() => setIsModalVisible(true)}>
        Add New Item
      </Button>
      <Table dataSource={hardwareItems} columns={columns} rowKey="id" />
      <Modal
        title="Manage Hardware Item"
        visible={isModalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          form.resetFields();
          setIsModalVisible(false);
        }}
      >
        <Form form={form} onFinish={form.getFieldValue('id') ? handleEdit : handleAdd}>
          <Form.Item name="id" hidden>
            <Input />
          </Form.Item>
          <Form.Item
            label="Name"
            name="name"
            rules={[{ required: true, message: 'Please enter the name' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            label="Type"
            name="type"
            rules={[{ required: true, message: 'Please enter the type' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            label="Quantity"
            name="quantity"
            rules={[{ required: true, message: 'Please enter the quantity' }]}
          >
            <Input type="number" />
          </Form.Item>
          <Form.Item
            label="Location"
            name="location"
            rules={[{ required: true, message: 'Please enter the location' }]}
          >
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default InventoryManagement;