import { NextResponse } from 'next/server';
import { testConnection } from '@/lib/database';

export async function GET() {
  try {
    const health = await testConnection();
    
    return NextResponse.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      database: {
        connected: health.connected,
        totalBooks: health.totalBooks,
        totalChunks: health.totalChunks,
        totalWords: health.totalWords
      },
      frontend: {
        status: 'operational',
        api: 'ready'
      }
    });
  } catch (error) {
    console.error('Health check failed:', error);
    
    return NextResponse.json({
      status: 'degraded',
      timestamp: new Date().toISOString(),
      database: {
        connected: false,
        error: 'Connection failed'
      },
      frontend: {
        status: 'operational',
        api: 'ready'
      }
    }, { status: 503 });
  }
}