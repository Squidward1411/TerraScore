'use client'

import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'

interface NDVIChartProps {
  parcelId: string
}

export default function NDVIChart({ parcelId }: NDVIChartProps) {
  // In production, this would fetch actual NDVI time series from the API
  // For now, we'll use mock data
  const { data, isLoading } = useQuery({
    queryKey: ['ndvi-history', parcelId],
    queryFn: async () => {
      // Mock data - replace with actual API call
      const mockData = generateMockNDVIData()
      return mockData
    },
  })

  if (isLoading) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="date"
          tickFormatter={(value) => format(new Date(value), 'MMM dd')}
          style={{ fontSize: '12px' }}
        />
        <YAxis
          domain={[0, 1]}
          ticks={[0, 0.2, 0.4, 0.6, 0.8, 1.0]}
          style={{ fontSize: '12px' }}
        />
        <Tooltip
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              return (
                <div className="bg-white p-3 shadow-lg rounded-lg border">
                  <p className="text-sm font-medium">
                    {format(new Date(payload[0].payload.date), 'MMM dd, yyyy')}
                  </p>
                  <p className="text-sm text-green-600">
                    NDVI: {payload[0].value?.toFixed(3)}
                  </p>
                  {payload[1] && (
                    <p className="text-sm text-blue-600">
                      EVI: {payload[1].value?.toFixed(3)}
                    </p>
                  )}
                </div>
              )
            }
            return null
          }}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="ndvi"
          stroke="#16a34a"
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
          name="NDVI"
        />
        <Line
          type="monotone"
          dataKey="evi"
          stroke="#2563eb"
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
          name="EVI"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

// Mock data generator - replace with actual API call
function generateMockNDVIData() {
  const data = []
  const startDate = new Date()
  startDate.setMonth(startDate.getMonth() - 6)

  for (let i = 0; i < 24; i++) {
    const date = new Date(startDate)
    date.setDate(date.getDate() + i * 7)

    // Simulate seasonal growth pattern
    const progress = i / 24
    const ndvi = 0.3 + 0.5 * Math.sin(progress * Math.PI) * (1 - Math.random() * 0.1)
    const evi = ndvi * 0.9 + Math.random() * 0.05

    data.push({
      date: date.toISOString(),
      ndvi: Math.min(Math.max(ndvi, 0), 1),
      evi: Math.min(Math.max(evi, 0), 1),
    })
  }

  return data
}
