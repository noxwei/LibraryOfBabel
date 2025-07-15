import { NextRequest, NextResponse } from 'next/server'

export async function GET() {
  try {
    const response = await fetch('http://localhost:8081/hr/alerts')
    if (!response.ok) {
      // Return mock data if alerts endpoint doesn't exist
      return NextResponse.json({
        alerts: [
          {
            alert_id: 'alert-001',
            agent_id: 'maya-qa',
            alert_type: 'performance_review',
            alert_data: { task: 'Quarterly QA review scheduled' },
            status: 'new',
            created_at: new Date().toISOString()
          }
        ]
      })
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('HR Alerts API Error:', error)
    // Return mock data on error
    return NextResponse.json({
      alerts: [
        {
          alert_id: 'alert-001',
          agent_id: 'maya-qa',
          alert_type: 'performance_review',
          alert_data: { task: 'Quarterly QA review scheduled' },
          status: 'new',
          created_at: new Date().toISOString()
        }
      ]
    })
  }
}