import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-b from-green-50 to-white">
      <div className="max-w-4xl text-center">
        <h1 className="text-6xl font-bold text-gray-900 mb-6">
          Terra<span className="text-green-600">Score</span>
        </h1>
        <p className="text-2xl text-gray-600 mb-8">
          Agricultural Risk Intelligence Platform
        </p>
        <p className="text-lg text-gray-500 mb-12 max-w-2xl mx-auto">
          Transform satellite imagery, weather data, and soil characteristics into
          financial-grade credit scores for farm parcels. Make informed lending
          decisions without physical site inspections.
        </p>

        <div className="flex gap-4 justify-center">
          <Link href="/dashboard">
            <Button size="lg" className="text-lg px-8">
              Go to Dashboard
            </Button>
          </Link>
          <Link href="/auth/login">
            <Button size="lg" variant="outline" className="text-lg px-8">
              Sign In
            </Button>
          </Link>
        </div>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="p-6 bg-white rounded-lg shadow-md">
            <div className="text-3xl mb-3">🛰️</div>
            <h3 className="text-xl font-semibold mb-2">Satellite Monitoring</h3>
            <p className="text-gray-600">
              Real-time crop health tracking using Sentinel-2 satellite imagery
            </p>
          </div>

          <div className="p-6 bg-white rounded-lg shadow-md">
            <div className="text-3xl mb-3">📊</div>
            <h3 className="text-xl font-semibold mb-2">Credit Scoring</h3>
            <p className="text-gray-600">
              AI-powered risk assessment combining multiple data sources
            </p>
          </div>

          <div className="p-6 bg-white rounded-lg shadow-md">
            <div className="text-3xl mb-3">⚡</div>
            <h3 className="text-xl font-semibold mb-2">Instant Decisions</h3>
            <p className="text-gray-600">
              Make lending decisions in minutes instead of weeks
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}
