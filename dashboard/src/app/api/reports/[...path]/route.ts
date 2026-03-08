import { NextRequest, NextResponse } from 'next/server';

// GitHub raw content URL for fetching reports
const GITHUB_RAW_BASE = 'https://raw.githubusercontent.com/vickey-kapoor/ai-research-whatsapp-digest/master/reports';

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  try {
    const filePath = params.path.join('/');

    // Validate path to prevent directory traversal
    if (filePath.includes('..')) {
      return new NextResponse('Invalid path', { status: 400 });
    }

    // Fetch from GitHub raw content
    const githubUrl = `${GITHUB_RAW_BASE}/${filePath}`;
    const response = await fetch(githubUrl);

    if (!response.ok) {
      return new NextResponse('File not found', { status: 404 });
    }

    const arrayBuffer = await response.arrayBuffer();

    let contentType = 'application/octet-stream';
    if (filePath.endsWith('.pdf')) {
      contentType = 'application/pdf';
    }

    return new NextResponse(arrayBuffer, {
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': `inline; filename="${filePath.split('/').pop()}"`,
        'Cache-Control': 'public, max-age=3600',
      },
    });
  } catch (error) {
    console.error('Error serving report:', error);
    return new NextResponse('Internal server error', { status: 500 });
  }
}
