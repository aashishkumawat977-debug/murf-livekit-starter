import { NextResponse } from 'next/server';
import { execFile } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execFileAsync = promisify(execFile);

export async function GET() {
  try {
    const projectRoot = path.resolve(process.cwd(), '..');
    const backendDir = path.join(projectRoot, 'backend');
    const python = path.join(backendDir, '.venv', 'Scripts', 'python.exe');

    const script = `
from src.call_analytics_db import get_call_counts
import json
print(json.dumps(get_call_counts()))
`;

    const { stdout } = await execFileAsync(
      python,
      ['-c', script],
      {
        cwd: backendDir,
      }
    );

    const data = JSON.parse(stdout.trim());

    const successRate =
      data.total > 0
        ? Math.round((data.successful / data.total) * 100)
        : 0;

    return NextResponse.json({
      ...data,
      successRate,
    });
  } catch (error) {
    console.error('Analytics API error:', error);

    return NextResponse.json(
      {
        error: 'Unable to load call analytics.',
      },
      {
        status: 500,
      }
    );
  }
}
