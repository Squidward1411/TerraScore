'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import Link from 'next/link'
import { Plus, Search, Filter, MapPin, TrendingUp, AlertTriangle } from 'lucide-react'

interface ParcelSimple {
  id: string
  cadastral_id: string
  parcel_name?: string
  area_hectares: number
  current_crop_type?: string
  current_health_score?: number
  municipality?: string
  is_active: boolean
}

export default function DashboardPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [cropFilter, setCropFilter] = useState('')
  const [page, setPage] = useState(1)

  // Fetch parcels
  const { data: parcelsData, isLoading } = useQuery({
    queryKey: ['parcels', page, searchQuery, cropFilter],
    queryFn: () =>
      apiClient.getParcels({
        page,
        page_size: 20,
        search: searchQuery || undefined,
        crop_type: cropFilter || undefined,
      }),
  })

  const getHealthColor = (score?: number) => {
    if (!score) return 'bg-gray-200'
    if (score >= 70) return 'bg-green-500'
    if (score >= 50) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const getHealthLabel = (score?: number) => {
    if (!score) return 'Unknown'
    if (score >= 70) return 'Good'
    if (score >= 50) return 'Fair'
    return 'Poor'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Parcel Dashboard
                </h1>
                <p className="mt-1 text-sm text-gray-500">
                  Monitor and assess agricultural parcels
                </p>
              </div>
              <Link href="/dashboard/parcels/new">
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Parcel
                </Button>
              </Link>
            </div>

            {/* Search and Filters */}
            <div className="mt-6 flex gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by cadastral ID or name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <select
                value={cropFilter}
                onChange={(e) => setCropFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
              >
                <option value="">All Crops</option>
                <option value="maize">Maize</option>
                <option value="wheat">Wheat</option>
                <option value="soybean">Soybean</option>
                <option value="sunflower">Sunflower</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Parcels"
            value={parcelsData?.total || 0}
            icon={<MapPin className="h-8 w-8 text-green-600" />}
            change="+2.5%"
          />
          <StatCard
            title="Avg Health Score"
            value="74.2"
            icon={<TrendingUp className="h-8 w-8 text-blue-600" />}
            change="+5.3%"
          />
          <StatCard
            title="Active Alerts"
            value="12"
            icon={<AlertTriangle className="h-8 w-8 text-yellow-600" />}
            change="-8.1%"
          />
          <StatCard
            title="Total Area"
            value="1,247 ha"
            icon={<MapPin className="h-8 w-8 text-purple-600" />}
            change="+12.0%"
          />
        </div>

        {/* Parcels Table */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">Your Parcels</h2>

            {isLoading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
                <p className="mt-2 text-gray-500">Loading parcels...</p>
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead>
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Cadastral ID
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Name
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Area
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Crop
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Health
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Location
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {parcelsData?.items.map((parcel: ParcelSimple) => (
                        <tr key={parcel.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {parcel.cadastral_id}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {parcel.parcel_name || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {parcel.area_hectares.toFixed(2)} ha
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">
                            {parcel.current_crop_type || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div
                                className={`h-2 w-2 rounded-full mr-2 ${getHealthColor(
                                  parcel.current_health_score
                                )}`}
                              ></div>
                              <span className="text-sm text-gray-900">
                                {parcel.current_health_score?.toFixed(1) || 'N/A'}
                              </span>
                              <span className="ml-2 text-xs text-gray-500">
                                ({getHealthLabel(parcel.current_health_score)})
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {parcel.municipality || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <Link
                              href={`/dashboard/parcels/${parcel.id}`}
                              className="text-green-600 hover:text-green-900"
                            >
                              View Details
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                {parcelsData && parcelsData.pages > 1 && (
                  <div className="flex items-center justify-between px-6 py-4 border-t">
                    <div className="text-sm text-gray-700">
                      Showing page {page} of {parcelsData.pages} ({parcelsData.total} total parcels)
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                      >
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => setPage((p) => Math.min(parcelsData.pages, p + 1))}
                        disabled={page === parcelsData.pages}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({
  title,
  value,
  icon,
  change,
}: {
  title: string
  value: string | number
  icon: React.ReactNode
  change: string
}) {
  const isPositive = change.startsWith('+')

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="mt-2 text-3xl font-semibold text-gray-900">{value}</p>
          <p
            className={`mt-2 text-sm ${
              isPositive ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {change} from last month
          </p>
        </div>
        <div className="flex-shrink-0">{icon}</div>
      </div>
    </div>
  )
}
