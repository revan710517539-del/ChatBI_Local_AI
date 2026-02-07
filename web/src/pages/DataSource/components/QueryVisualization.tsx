import React, { useMemo, useState, useRef, useEffect } from 'react';
import { Card, Select, Space, Empty, Typography, Alert } from 'antd';
import { Column, Line, Pie, Scatter, Area } from '@antv/g2plot';
import {
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  DotChartOutlined,
  AreaChartOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

type QueryVisualizationProps = {
  result: {
    columns: string[];
    data: any[];
  };
};

const QueryVisualization: React.FC<QueryVisualizationProps> = ({ result }) => {
  const [chartType, setChartType] = useState<string>('bar');
  const [xAxis, setXAxis] = useState<string>('');
  const [yAxis, setYAxis] = useState<string>('');
  const containerRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<any>(null);

  // Detect column types
  const columnTypes = useMemo(() => {
    const types: Record<string, 'numeric' | 'categorical' | 'datetime'> = {};

    result.columns.forEach((col) => {
      const values = result.data
        .map((row) => row[col])
        .filter((v) => v !== null && v !== undefined);

      if (values.length === 0) {
        types[col] = 'categorical';
        return;
      }

      const firstValue = values[0];

      // Check if numeric
      if (typeof firstValue === 'number' || !isNaN(Number(firstValue))) {
        types[col] = 'numeric';
      }
      // Check if datetime
      else if (firstValue instanceof Date || !isNaN(Date.parse(firstValue))) {
        types[col] = 'datetime';
      }
      // Default to categorical
      else {
        types[col] = 'categorical';
      }
    });

    return types;
  }, [result.columns, result.data]);

  // Get suitable columns for X and Y axes
  const categoricalColumns = useMemo(
    () => result.columns.filter((col) => columnTypes[col] === 'categorical'),
    [result.columns, columnTypes],
  );

  const numericColumns = useMemo(
    () => result.columns.filter((col) => columnTypes[col] === 'numeric'),
    [result.columns, columnTypes],
  );

  // Auto-select default axes
  React.useEffect(() => {
    if (!xAxis && categoricalColumns.length > 0) {
      setXAxis(categoricalColumns[0] || '');
    }
    if (!yAxis && numericColumns.length > 0) {
      setYAxis(numericColumns[0] || '');
    }
  }, [categoricalColumns, numericColumns]);

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!xAxis || !yAxis) return [];

    return result.data.map((row) => ({
      [xAxis]: String(row[xAxis]),
      [yAxis]: Number(row[yAxis]) || 0,
    }));
  }, [result.data, xAxis, yAxis]);

  useEffect(() => {
    if (!containerRef.current || chartData.length === 0 || !xAxis || !yAxis) {
      return;
    }

    // Cleanup previous chart
    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    const commonConfig = {
      data: chartData,
      xField: xAxis,
      yField: yAxis,
      appendPadding: 10,
      autoFit: true,
    };

    let chart: any;

    try {
      switch (chartType) {
        case 'bar':
          chart = new Column(containerRef.current, commonConfig);
          break;
        case 'line':
          chart = new Line(containerRef.current, commonConfig);
          break;
        case 'pie':
          chart = new Pie(containerRef.current, {
            data: chartData,
            angleField: yAxis,
            colorField: xAxis,
            appendPadding: 10,
            autoFit: true,
            radius: 0.8,
            label: {
              type: 'inner',
              offset: '-30%',
              content: ({ percent }: any) => `${(percent * 100).toFixed(0)}%`,
              style: {
                fontSize: 14,
                textAlign: 'center',
              },
            },
          });
          break;
        case 'scatter':
          chart = new Scatter(containerRef.current, commonConfig);
          break;
        case 'area':
          chart = new Area(containerRef.current, commonConfig);
          break;
      }

      if (chart) {
        chart.render();
        chartInstance.current = chart;
      }
    } catch (error) {
      console.error('Failed to render chart:', error);
    }

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [chartType, xAxis, yAxis, chartData]);

  if (categoricalColumns.length === 0 || numericColumns.length === 0) {
    return (
      <Alert
        message="Visualization Not Available"
        description="Query results must contain at least one categorical column and one numeric column for visualization."
        type="info"
        showIcon
      />
    );
  }

  const renderChart = () => {
    return (
      <div
        ref={containerRef}
        style={{
          height: '100%',
          minHeight: 400,
          width: '100%',
          padding: 16,
        }}
      />
    );
  };

  return (
    <Card>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* Chart Controls */}
        <Space wrap>
          <Select
            value={chartType}
            onChange={setChartType}
            style={{ width: 150 }}
            options={[
              { label: 'Bar Chart', value: 'bar', icon: <BarChartOutlined /> },
              {
                label: 'Line Chart',
                value: 'line',
                icon: <LineChartOutlined />,
              },
              { label: 'Pie Chart', value: 'pie', icon: <PieChartOutlined /> },
              {
                label: 'Scatter Plot',
                value: 'scatter',
                icon: <DotChartOutlined />,
              },
              {
                label: 'Area Chart',
                value: 'area',
                icon: <AreaChartOutlined />,
              },
            ]}
          />

          <Select
            value={xAxis}
            onChange={setXAxis}
            style={{ width: 200 }}
            placeholder="Select X-Axis"
            options={categoricalColumns.map((col) => ({
              label: `${col} (categorical)`,
              value: col,
            }))}
          />

          <Select
            value={yAxis}
            onChange={setYAxis}
            style={{ width: 200 }}
            placeholder="Select Y-Axis"
            options={numericColumns.map((col) => ({
              label: `${col} (numeric)`,
              value: col,
            }))}
          />
        </Space>

        {/* Chart Display */}
        {xAxis && yAxis ? (
          renderChart()
        ) : (
          <Empty description="Please select both X and Y axes" />
        )}
      </Space>
    </Card>
  );
};

export default QueryVisualization;
