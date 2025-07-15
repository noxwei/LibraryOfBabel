import { NextRequest, NextResponse } from 'next/server'

export async function GET() {
  try {
    const response = await fetch('http://localhost:8082/hr/qa/training')
    if (!response.ok) {
      throw new Error(`Maya QA Agent error: ${response.status}`)
    }
    const rawData = await response.json()
    
    // Transform the data structure to match frontend expectations
    const transformedData = {
      training: {
        programs: rawData.cross_training?.active_programs?.map(program => ({
          name: program.program,
          description: `Led by ${program.trainer} with ${program.participants.length} participants`,
          status: 'active',
          duration: '6 weeks',
          participants: program.participants.length,
          completion_rate: program.completion_rate
        })) || [],
        schedule: {
          'This Week': rawData.cross_training?.active_programs?.map(program => ({
            time: new Date(program.next_session).toLocaleTimeString(),
            topic: program.program,
            trainer: program.trainer
          })) || [],
          'Next Week': [
            {
              time: '10:00 AM',
              topic: 'Advanced Testing Strategies',
              trainer: 'Maya Rodriguez'
            }
          ]
        },
        certifications: rawData.cross_training?.upcoming_certifications || []
      },
      generated_by: rawData.generated_by,
      timestamp: rawData.timestamp
    }
    
    return NextResponse.json(transformedData)
  } catch (error) {
    console.error('QA Training API Error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch QA training data' },
      { status: 500 }
    )
  }
}