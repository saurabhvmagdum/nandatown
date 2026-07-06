import { readFile } from "node:fs/promises";
import path from "node:path";

// Serves showcase video uploads stored on the host's uploads volume.
export const dynamic = "force-dynamic";

const UPLOAD_DIR = process.env.SHOWCASE_UPLOAD_DIR ?? "/data/uploads";
const MIME: Record<string, string> = {
  ".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm",
  ".m4v": "video/x-m4v", ".mkv": "video/x-matroska", ".avi": "video/x-msvideo",
  ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
  ".gif": "image/gif", ".pdf": "application/pdf",
};

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ name: string }> },
) {
  const { name } = await params;
  const safe = path.basename(name);
  try {
    const buf = await readFile(path.join(UPLOAD_DIR, safe));
    const type = MIME[path.extname(safe).toLowerCase()] ?? "application/octet-stream";
    return new Response(new Uint8Array(buf), {
      headers: { "Content-Type": type, "Cache-Control": "public, max-age=3600" },
    });
  } catch {
    return new Response("Not found", { status: 404 });
  }
}
