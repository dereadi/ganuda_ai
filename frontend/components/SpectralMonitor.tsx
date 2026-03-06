import React, { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface SpectralData {
  frequency: number;
  amplitude: number;
}

interface SpectralMonitorProps {
  data: SpectralData[];
  title?: string;
}

const SpectralMonitor: React.FC<SpectralMonitorProps> = ({ data, title = 'Spectral Monitor' }) => {
  const [chartData, setChartData] = useState({
    labels: data.map((d) => d.frequency),
    datasets: [
      {
        label: 'Amplitude',
        data: data.map((d) => d.amplitude),
        fill: false,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
    ],
  });

  useEffect(() => {
    setChartData({
      labels: data.map((d) => d.frequency),
      datasets: [
        {
          label: 'Amplitude',
          data: data.map((d) => d.amplitude),
          fill: false,
          borderColor: 'rgb(75, 192, 192)',
          tension: 0.1,
        },
      ],
    });
  }, [data]);

  return (
    <div>
      <h2>{title}</h2>
      <Line data={chartData} />
    </div>
  );
};

export default SpectralMonitor;