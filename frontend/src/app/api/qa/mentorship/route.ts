import { NextRequest, NextResponse } from 'next/server'

export async function GET() {
  try {
    const response = await fetch('http://localhost:8082/hr/qa/mentorship')
    if (!response.ok) {
      throw new Error(`Maya QA Agent error: ${response.status}`)
    }
    const rawData = await response.json()
    
    // Transform the data structure to match frontend expectations
    const transformedData = {
      mentorship: {
        mentor_pairs: rawData.mentorship_program?.active_pairs?.map(pair => ({
          mentor: pair.mentor,
          mentee: pair.mentee,
          focus_area: pair.focus_areas.join(', '),
          progress: pair.progress === 'excellent' ? 95 : pair.progress === 'good' ? 80 : 70,
          sessions_completed: pair.sessions_completed,
          next_meeting: pair.next_meeting
        })) || [],
        programs: [
          {
            name: 'QA Mentorship Program',
            description: 'Comprehensive mentorship program for QA excellence',
            participants: rawData.mentorship_program?.program_stats?.total_mentees || 5,
            success_rate: rawData.mentorship_program?.program_stats?.completion_rate || '92%'
          },
          {
            name: 'HR Leadership Development',
            description: 'Developing next generation HR leaders',
            participants: 3,
            success_rate: '95%'
          }
        ],
        stats: rawData.mentorship_program?.program_stats,
        success_stories: rawData.mentorship_program?.success_stories || []
      },
      generated_by: rawData.generated_by,
      timestamp: rawData.timestamp
    }
    
    return NextResponse.json(transformedData)
  } catch (error) {
    console.error('QA Mentorship API Error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch QA mentorship data' },
      { status: 500 }
    )
  }
}