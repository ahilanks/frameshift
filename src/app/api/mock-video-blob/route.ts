import { NextResponse } from 'next/server';

export async function GET() {
  // Create a minimal MP4 video blob (just headers, not a real video)
  // In reality this would be a blob URL from uploaded file
  const mockVideoData = new Uint8Array([
    0x00, 0x00, 0x00, 0x20, 0x66, 0x74, 0x79, 0x70, // MP4 header start
    0x69, 0x73, 0x6F, 0x6D, 0x00, 0x00, 0x02, 0x00,
    0x69, 0x73, 0x6F, 0x6D, 0x69, 0x73, 0x6F, 0x32,
    0x61, 0x76, 0x63, 0x31, 0x6D, 0x70, 0x34, 0x31
  ]);

  console.log('🎥 MOCK VIDEO: Serving mock video blob');

  return new NextResponse(mockVideoData, {
    status: 200,
    headers: {
      'Content-Type': 'video/mp4',
      'Content-Length': mockVideoData.length.toString(),
      'Cache-Control': 'no-cache'
    },
  });
}