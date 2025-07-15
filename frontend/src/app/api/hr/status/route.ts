import { NextRequest, NextResponse } from 'next/server'

export async function GET() {
  try {
    const response = await fetch('http://localhost:8081/hr/status')
    if (!response.ok) {
      throw new Error(`HR Agent error: ${response.status}`)
    }
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('HR Status API Error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch HR status' },
      { status: 500 }
    )
  }
}