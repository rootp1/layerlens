import * as React from 'react';
import { BarChart } from '@mui/x-charts/BarChart';

const chartSetting = {
  xAxis: [
    {
      label: 'wasted bytes',
    },
  ],
  width: 500,
  height: 160,
};

const valueFormatter = (value) => `${value?.toLocaleString?.() ?? value} bytes`;

export default function HorizontalBars({ data }) {
  return (
    <BarChart
      dataset={[{ image: data, label: 'image' }]}
      yAxis={[{ scaleType: 'band', dataKey: 'label' }]}
      series={[{ dataKey: 'image', valueFormatter, color: '#22d3ee' }]}
      layout="horizontal"
      sx={{
        '& .MuiChartsAxis-line, & .MuiChartsAxis-tick': { stroke: '#3f3f5a' },
        '& .MuiChartsAxis-tickLabel': { fill: '#a1a1b5' },
        '& .MuiChartsAxis-label': { fill: '#e6e6f0' },
        '& .MuiBarElement-root': { filter: 'drop-shadow(0 0 6px rgba(34,211,238,0.5))' },
      }}
      {...chartSetting}
    />
  );
}
