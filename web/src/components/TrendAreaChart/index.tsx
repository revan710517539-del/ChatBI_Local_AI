import React from 'react';
import { Empty, Space, Tag } from 'antd';

type SeriesConfig = {
  key: string;
  name: string;
  color: string;
  fill?: string;
};

type TrendAreaChartProps = {
  data: Record<string, any>[];
  xKey?: string;
  series: SeriesConfig[];
  height?: number;
};

const TrendAreaChart: React.FC<TrendAreaChartProps> = ({
  data,
  xKey = 'date',
  series,
  height = 280,
}) => {
  if (!data?.length || !series?.length) {
    return <Empty description="暂无趋势数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />;
  }

  const width = 980;
  const padTop = 18;
  const padBottom = 40;
  const padLeft = 48;
  const padRight = 16;

  const values: number[] = [];
  for (const row of data) {
    for (const s of series) {
      const v = Number(row[s.key]);
      if (Number.isFinite(v)) values.push(v);
    }
  }
  let min = Math.min(...values);
  let max = Math.max(...values);
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    min = 0;
    max = 1;
  }
  if (min === max) {
    min -= 1;
    max += 1;
  }

  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;
  const yBase = padTop + chartH;

  const xPos = (idx: number) => {
    if (data.length === 1) return padLeft + chartW / 2;
    return padLeft + (idx / (data.length - 1)) * chartW;
  };
  const yPos = (val: number) => {
    const ratio = (val - min) / (max - min);
    return yBase - ratio * chartH;
  };

  const gridLines = 4;
  const yTicks = Array.from({ length: gridLines + 1 }, (_, i) => {
    const ratio = i / gridLines;
    const y = padTop + ratio * chartH;
    const v = max - ratio * (max - min);
    return { y, v };
  });

  const labelInterval = Math.max(1, Math.floor(data.length / 6));

  return (
    <div style={{ width: '100%' }}>
      <Space size={10} style={{ marginBottom: 10 }} wrap>
        {series.map((s) => (
          <Tag key={s.key} color={s.color} style={{ borderRadius: 999 }}>
            {s.name}
          </Tag>
        ))}
      </Space>

      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height}>
        <rect x={0} y={0} width={width} height={height} fill="transparent" />

        {yTicks.map((tick, i) => (
          <g key={`y-${i}`}>
            <line
              x1={padLeft}
              y1={tick.y}
              x2={width - padRight}
              y2={tick.y}
              stroke="#e6edf3"
              strokeWidth={1}
            />
            <text
              x={padLeft - 8}
              y={tick.y + 4}
              textAnchor="end"
              fontSize={11}
              fill="#64748b"
            >
              {tick.v.toFixed(3)}
            </text>
          </g>
        ))}

        {series.map((s) => {
          const points = data
            .map((row, idx) => {
              const v = Number(row[s.key]);
              return Number.isFinite(v) ? `${xPos(idx)},${yPos(v)}` : '';
            })
            .filter(Boolean);

          if (!points.length) return null;

          const firstX = xPos(0);
          const lastX = xPos(data.length - 1);
          const areaD = `M ${firstX} ${yBase} L ${points.join(' L ')} L ${lastX} ${yBase} Z`;

          return (
            <g key={s.key}>
              <path
                d={areaD}
                fill={s.fill || `${s.color}20`}
                stroke="none"
              />
              <polyline
                points={points.join(' ')}
                fill="none"
                stroke={s.color}
                strokeWidth={2.2}
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            </g>
          );
        })}

        {data.map((row, idx) => {
          if (idx % labelInterval !== 0 && idx !== data.length - 1) return null;
          const x = xPos(idx);
          return (
            <text
              key={`x-${idx}`}
              x={x}
              y={height - 14}
              textAnchor="middle"
              fontSize={11}
              fill="#64748b"
            >
              {String(row[xKey] || '')}
            </text>
          );
        })}
      </svg>
    </div>
  );
};

export default TrendAreaChart;
