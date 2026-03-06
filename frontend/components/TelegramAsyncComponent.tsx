import React, { useState, useEffect } from 'react';
import { TelegramClient, Api } from 'telegram';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorAlert } from '../common/ErrorAlert';

interface TelegramAsyncComponentProps {
  apiId: number;
  apiHash: string;
  phoneNumber: string;
  onMessageReceived: (message: string) => void;
}

const TelegramAsyncComponent: React.FC<TelegramAsyncComponentProps> = ({ apiId, apiHash, phoneNumber, onMessageReceived }) => {
  const [client, setClient] = useState<TelegramClient | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initializeClient = async () => {
      try {
        setLoading(true);
        const client = new TelegramClient(
          new Api.TelegramBaseClient({
            dcId: 2,
            testMode: false,
            connection: Api.ConnectionTcpFull,
            proxy: undefined,
          }),
          apiId,
          apiHash,
          { phoneNumber }
        );

        await client.connect();
        setClient(client);
      } catch (err) {
        setError(`Failed to connect to Telegram: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    initializeClient();
  }, [apiId, apiHash, phoneNumber]);

  useEffect(() => {
    if (client) {
      const handleNewMessage = async (update: Api.Update) => {
        if (update instanceof Api.UpdateNewMessage) {
          const message = update.message.message;
          onMessageReceived(message);
        }
      };

      client.addUpdateHandler(handleNewMessage);

      return () => {
        client.removeUpdateHandler(handleNewMessage);
      };
    }
  }, [client, onMessageReceived]);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorAlert message={error} />;
  }

  return (
    <div>
      <p>Telegram client is connected and listening for messages.</p>
    </div>
  );
};

export default TelegramAsyncComponent;