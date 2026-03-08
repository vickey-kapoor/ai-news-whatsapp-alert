import { NextRequest, NextResponse } from 'next/server';

const DEFAULT_REPO = 'vickey-kapoor/ai-research-whatsapp-digest';

async function fetchReportFromGithub(path: string): Promise<Response | null> {
  const base = `https://raw.githubusercontent.com/${DEFAULT_REPO}`;
  const branchesToTry = ['master', 'main'];

  for (const branch of branchesToTry) {
    const githubUrl = `${base}/${branch}/reports/${path}`;
    const response = await fetch(githubUrl, {
      next: { revalidate: 3600 },
    });

    if (response.ok) {
      return response;
    }
  }

  return null;
}

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const resolvedParams = await params;
    const filePath = resolvedParams.path.join('/').replace(/^reports\//, '');

    if (filePath.includes('..')) {
      return new NextResponse('Invalid path', { status: 400 });
    }

    const response = await fetchReportFromGithub(filePath);

    if (!response) {
      return new NextResponse('File not found', { status: 404 });
    }

    const arrayBuffer = await response.arrayBuffer();
    const contentType = filePath.endsWith('.pdf') ? 'application/pdf' : 'application/octet-stream';

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
