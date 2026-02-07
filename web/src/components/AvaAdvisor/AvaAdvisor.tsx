import { Advisor } from '@antv/ava';
import { Empty, Spin } from 'antd';
import React, { createRef, useEffect, useState } from 'react';

import G2Chart from '../G2Chart/G2Chart';
import AvaInsight from './AvaInsight';

interface AvaAdvisorProps {
  data: Record<string, any>[];
}

const AvaAdvisor: React.FC<AvaAdvisorProps> = ({ data }) => {
  const chartRef = createRef<HTMLDivElement>();
  const [adviseResults, setAdviseResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function getAdvise() {
      // 数据为空时不进行处理
      if (!data || data.length === 0) {
        setAdviseResults([]);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const chatAdvisor = new Advisor();
        const results = chatAdvisor.advise({
          data: data, // 使用实际数据而不是 demo 数据
          options: {
            showLog: false, // 生产环境关闭日志
          },
        });

        console.log('AVA Advisor Results:', results);
        setAdviseResults(results);
      } catch (err) {
        console.error('AVA Advisor Error:', err);
        setError(err instanceof Error ? err.message : '图表生成失败');
      } finally {
        setLoading(false);
      }
    }

    getAdvise();
  }, [data]);

  // 加载状态
  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <Spin size="large" tip="正在生成可视化图表..." />
      </div>
    );
  }

  // 错误状态
  if (error) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <Empty description={error} />
      </div>
    );
  }

  // 无数据状态
  if (!data || data.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <Empty description="暂无数据" />
      </div>
    );
  }

  return (
    <div className="w-full h-full overflow-hidden box-border p-4">
      {adviseResults[0] ? (
        <G2Chart
          className="bg-white"
          chartRef={chartRef}
          spec={adviseResults[0]?.spec}
        />
      ) : (
        <AvaInsight data={data} />
      )}
    </div>
  );
};

export default AvaAdvisor;
