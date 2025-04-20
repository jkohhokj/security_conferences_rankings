'use client';

import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, LabelList,
} from 'recharts';

interface InstitutionData {
  [institution: string]: number;
}

export default function InstitutionFrequencyChart() {
  const [data, setData] = useState<{ name: string; count: number }[]>([]);
  const [yearStart, setYearStart] = useState(2020);
  const [yearEnd, setYearEnd] = useState(2022);

  // Debounced effect to avoid firing on every small change
  useEffect(() => {
    const controller = new AbortController();
    const signal = controller.signal;

    const timeout = setTimeout(() => {
      const fetchData = async () => {
        try {
          const res = await fetch(`/api/usenix_ranking?year_start=${yearStart}&year_end=${yearEnd}`, { signal });
          const json = await res.json();
          const rawData: InstitutionData = json.data;

          const formattedData = Object.entries(rawData)
            .map(([name, count]) => ({ name, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 15);

          setData(formattedData);
        } catch (error) {
          if (error.name !== 'AbortError') {
            console.error('Failed to fetch institution data:', error);
          }
        }
      };

      fetchData();
    }, 300); // Debounce delay

    return () => {
      clearTimeout(timeout);
      controller.abort();
    };
  }, [yearStart, yearEnd]);

  return (
    <div className="w-full p-4">
      <h2 className="text-xl font-bold mb-4 text-center">Top Institutions by USENIX Papers</h2>

      {/* Slider Controls */}
      <div className="flex flex-col md:flex-row items-center justify-center gap-6 mb-6">
        <div className="flex flex-col items-center">
          <label className="font-medium mb-1">Start Year: {yearStart}</label>
          <input
            type="range"
            min={2000}
            max={2025}
            value={yearStart}
            onChange={(e) => setYearStart(Number(e.target.value))}
            className="w-64"
          />
        </div>
        <div className="flex flex-col items-center">
          <label className="font-medium mb-1">End Year: {yearEnd}</label>
          <input
            type="range"
            min={2000}
            max={2025}
            value={yearEnd}
            onChange={(e) => setYearEnd(Number(e.target.value))}
            className="w-64"
          />
        </div>
      </div>

      {/* Chart */}
      <div className="w-full h-[600px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 20, right: 40, left: 80, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis type="category" dataKey="name" width={250} />
            <Tooltip />
            <Bar dataKey="count" fill="#8884d8">
              <LabelList dataKey="count" position="right" />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
