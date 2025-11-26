'use client'

import { useQuery } from '@tanstack/react-query'
import { useParams } from 'next/navigation'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import {
  MapPin,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Download,
  RefreshCw,
} from 'lucide-react'
import { formatCurrency, formatDate, getRiskColor, getScoreColor } from '@/lib/utils'
import NDVIChart from '@/components/charts/NDVIChart'

export default function ParcelDetailPage() {
  const params = useParams()
  const parcelId = params.id as string

  // Fetch parcel details
  const { data: parcel, isLoading: parcelLoading } = useQuery({
    queryKey: ['parcel', parcelId],
    queryFn: () => apiClient.getParcel(parcelId),
  })

  // Fetch credit score
  const { data: creditScore, isLoading: scoreLoading, refetch: refetchScore } = useQuery({
    queryKey: ['credit-score', parcelId],
    queryFn: () => apiClient.getCreditScore(parcelId),
  })

  // Fetch health status
  const { data: health } = useQuery({
    queryKey: ['parcel-health', parcelId],
    queryFn: () => apiClient.getParcelHealth(parcelId),
  })

  // Fetch risks
  const { data: risks } = useQuery({
    queryKey: ['parcel-risks', parcelId],
    queryFn: () => apiClient.getParcelRisks(parcelId),
  })

  if (parcelLoading || scoreLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
          <p className="mt-4 text-gray-500">Loading parcel data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {parcel?.parcel_name || parcel?.cadastral_id}
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                Cadastral ID: {parcel?.cadastral_id} • {parcel?.area_hectares.toFixed(2)} hectares
              </p>
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => refetchScore()}
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Recalculate
              </Button>
              <Button>
                <Download className="mr-2 h-4 w-4" />
                Export Report
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Credit Score Card */}
        <div className="bg-white rounded-lg shadow p-8 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Overall Score */}
            <div className="text-center">
              <p className="text-sm font-medium text-gray-600 uppercase tracking-wide">
                Credit Score
              </p>
              <div className="mt-4">
                <div className={`text-6xl font-bold ${getScoreColor(creditScore?.score || 0)}`}>
                  {creditScore?.score.toFixed(1)}
                </div>
                <div className="mt-2">
                  <span
                    className={`inline-flex px-3 py-1 rounded-full text-sm font-semibold ${getRiskColor(
                      creditScore?.risk_category
                    )}`}
                  >
                    {creditScore?.risk_category} RISK
                  </span>
                </div>
                {creditScore?.score_change && (
                  <div className="mt-2 flex items-center justify-center text-sm">
                    {creditScore.score_change > 0 ? (
                      <>
                        <TrendingUp className="h-4 w-4 text-green-600 mr-1" />
                        <span className="text-green-600">
                          +{creditScore.score_change.toFixed(1)} from last calculation
                        </span>
                      </>
                    ) : (
                      <>
                        <TrendingDown className="h-4 w-4 text-red-600 mr-1" />
                        <span className="text-red-600">
                          {creditScore.score_change.toFixed(1)} from last calculation
                        </span>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Component Scores */}
            <div className="col-span-2">
              <p className="text-sm font-medium text-gray-600 uppercase tracking-wide mb-4">
                Score Components
              </p>
              <div className="space-y-4">
                <ScoreBar
                  label="Crop Health"
                  score={creditScore?.components.crop_health || 0}
                  weight="40%"
                />
                <ScoreBar
                  label="Weather Risk"
                  score={creditScore?.components.weather_risk || 0}
                  weight="30%"
                />
                <ScoreBar
                  label="Soil Quality"
                  score={creditScore?.components.soil_quality || 0}
                  weight="15%"
                />
                <ScoreBar
                  label="Historical Performance"
                  score={creditScore?.components.historical || 0}
                  weight="15%"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column */}
          <div className="space-y-8">
            {/* Yield Prediction */}
            {creditScore?.yield_prediction && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Yield Prediction</h3>
                <div className="text-center py-4">
                  <div className="text-4xl font-bold text-gray-900">
                    {creditScore.yield_prediction.predicted_yield_tons_per_ha.toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">tons per hectare</div>
                  <div className="mt-4 flex items-center justify-center text-sm text-gray-600">
                    <span>
                      Range: {creditScore.yield_prediction.lower_bound?.toFixed(2)} -{' '}
                      {creditScore.yield_prediction.upper_bound?.toFixed(2)} tons/ha
                    </span>
                  </div>
                  <div className="mt-2 text-sm text-gray-500">
                    Confidence: {((creditScore.yield_prediction.confidence || 0) * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            )}

            {/* Loan Recommendation */}
            {creditScore?.loan_recommendation && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">Loan Recommendation</h3>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-600">Recommended Amount</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatCurrency(creditScore.loan_recommendation.recommended_amount)}
                    </p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Interest Adjustment</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {creditScore.loan_recommendation.suggested_interest_adjustment > 0 ? '+' : ''}
                        {creditScore.loan_recommendation.suggested_interest_adjustment.toFixed(2)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Max LTV Ratio</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {creditScore.loan_recommendation.max_loan_to_value_ratio.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Active Risks */}
            {creditScore?.active_risk_factors && creditScore.active_risk_factors.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2" />
                  Active Risk Factors
                </h3>
                <div className="space-y-2">
                  {creditScore.active_risk_factors.map((risk, idx) => (
                    <div
                      key={idx}
                      className="flex items-center p-3 bg-yellow-50 rounded-md border border-yellow-200"
                    >
                      <AlertTriangle className="h-4 w-4 text-yellow-600 mr-2 flex-shrink-0" />
                      <span className="text-sm text-gray-900">{risk.replace(/_/g, ' ')}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column */}
          <div className="space-y-8">
            {/* NDVI Chart */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Crop Health Trend (NDVI)</h3>
              <NDVIChart parcelId={parcelId} />
            </div>

            {/* Parcel Information */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Parcel Information</h3>
              <div className="space-y-3">
                <InfoRow label="Current Crop" value={parcel?.current_crop_type || 'Not specified'} />
                <InfoRow label="Area" value={`${parcel?.area_hectares.toFixed(2)} hectares`} />
                <InfoRow label="Location" value={parcel?.municipality || 'Not specified'} />
                <InfoRow label="Soil Type" value={parcel?.soil_type || 'Not specified'} />
                <InfoRow
                  label="Irrigation"
                  value={parcel?.has_irrigation ? 'Yes' : 'No'}
                />
                {parcel?.planting_date && (
                  <InfoRow label="Planted" value={formatDate(parcel.planting_date)} />
                )}
              </div>
            </div>

            {/* Metadata */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Score Metadata</h3>
              <div className="space-y-3 text-sm">
                <InfoRow
                  label="Calculated"
                  value={creditScore?.calculated_at ? formatDate(creditScore.calculated_at) : 'N/A'}
                />
                <InfoRow
                  label="Confidence"
                  value={creditScore?.confidence_level || 'N/A'}
                />
                <InfoRow
                  label="Model Version"
                  value={creditScore?.model_version || '1.0.0'}
                />
                <InfoRow
                  label="Data Quality"
                  value={
                    creditScore?.data_quality_score
                      ? `${creditScore.data_quality_score.toFixed(0)}%`
                      : 'N/A'
                  }
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ScoreBar({ label, score, weight }: { label: string; score: number; weight: string }) {
  const getColor = (score: number) => {
    if (score >= 70) return 'bg-green-500'
    if (score >= 50) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium text-gray-700">{label}</span>
        <span className="text-gray-600">
          {score.toFixed(1)} <span className="text-gray-400">• {weight}</span>
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${getColor(score)}`}
          style={{ width: `${score}%` }}
        ></div>
      </div>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-600">{label}</span>
      <span className="font-medium text-gray-900">{value}</span>
    </div>
  )
}
