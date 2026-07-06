import type { NextRequest } from "next/server";
import { randomUUID } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { sql } from "@/lib/db";
import { createSkill } from "@/lib/skills";

// Showcase backend for the migrated NandaHack guide pages: submissions live
// in the same Postgres instance as the skills registry and uploads are
// stored on disk. Speaks the exact protocol of the previous Apps Script
// deployment so the static pages only needed their endpoint constant
// swapped.
export const dynamic = "force-dynamic";

const TYPES = ["code", "live", "video", "writeup"];
const PATHS = ["individual", "startup", "corporate"];
const UPLOAD_DIR = process.env.SHOWCASE_UPLOAD_DIR ?? "/data/uploads";

type Row = Record<string, unknown>;

let ready: Promise<void> | null = null;
function ensureShowcaseSchema(): Promise<void> {
  if (!ready) {
    const db = sql();
    ready = db`
      create table if not exists showcase (
        id               text primary key,
        status           text not null default 'pending',
        submitted_at     timestamptz not null default now(),
        approved_at      timestamptz,
        name             text not null,
        author           text not null,
        description      text not null,
        submission_type  text not null,
        contributor_path text not null,
        url              text,
        content          text,
        endpoints        text,
        tags             text,
        town_registry_id text
      )
    `.then(() => undefined);
  }
  return ready;
}

function json(obj: unknown) {
  return Response.json(obj);
}

function adminOk(key: unknown): boolean {
  const expected = process.env.SHOWCASE_ADMIN_KEY || "";
  return Boolean(expected) && String(key ?? "") === expected;
}

export async function GET(request: NextRequest) {
  try {
    await ensureShowcaseSchema();
    const db = sql();
    const p = request.nextUrl.searchParams;
    const action = p.get("action");
    if (action === "approved") {
      const rows = (await db`select * from showcase where status = 'approved' order by submitted_at desc`) as Row[];
      return json({ count: rows.length, approved: rows });
    }
    if (action === "pending") {
      if (!adminOk(p.get("admin_key"))) return json({ error: "Invalid admin key." });
      const rows = (await db`select * from showcase where status = 'pending' order by submitted_at desc`) as Row[];
      return json({ count: rows.length, pending: rows });
    }
    return json({ service: "nanda-showcase", storage: "postgres",
                  use: "GET ?action=approved | POST {action: submit|approve|reject}" });
  } catch (err) {
    return json({ error: String(err instanceof Error ? err.message : err) });
  }
}

export async function POST(request: NextRequest) {
  try {
    await ensureShowcaseSchema();
    const body = (await request.json()) as Row;
    if (body.action === "submit") return await submit(body);
    if (body.action === "approve") return await approve(body);
    if (body.action === "reject") return await reject(body);
    return json({ error: "Unknown action. Use submit | approve | reject." });
  } catch (err) {
    return json({ error: String(err instanceof Error ? err.message : err) });
  }
}

async function submit(b: Row) {
  const sub = String(b.submission_type ?? "");
  if (!TYPES.includes(sub)) return json({ error: "submission_type must be one of " + TYPES.join(" | ") });
  let cpath = String(b.contributor_path ?? "");
  if (!PATHS.includes(cpath)) cpath = "individual";
  if (!b.name || String(b.name).length < 2) return json({ error: "Give your project a name." });
  if (!b.author || String(b.author).length < 2) return json({ error: "Tell us who you are." });
  if (!b.description || String(b.description).length < 10) return json({ error: "The description needs at least a sentence." });

  const id = randomUUID().replace(/-/g, "").slice(0, 12);
  let url: string | null = b.url ? String(b.url) : null;

  // Optional direct video upload: {file_name, file_type, file_data (base64)}
  // is written to the uploads volume and served from /uploads/<name>.
  if (b.file_data && b.file_name) {
    const bytes = Buffer.from(String(b.file_data), "base64");
    if (bytes.length > 30 * 1024 * 1024) return json({ error: "Uploads are capped at 30 MB. Host bigger videos on YouTube or Drive and paste the link." });
    const safe = String(b.file_name).replace(/[^a-zA-Z0-9._-]/g, "_").slice(-80) || "upload.bin";
    const stored = id + "-" + safe;
    await mkdir(UPLOAD_DIR, { recursive: true });
    await writeFile(path.join(UPLOAD_DIR, stored), bytes);
    url = "/uploads/" + stored;
  }

  if ((sub === "code" || sub === "live" || sub === "video")
      && !(url && (url.indexOf("http") === 0 || url.indexOf("/uploads/") === 0))) {
    return json({ error: "A full http(s) URL is required for this submission type." });
  }
  if (sub === "writeup" && (!b.content || String(b.content).length < 50)) {
    return json({ error: "The written case needs some substance." });
  }

  const db = sql();
  await db`
    insert into showcase (id, status, name, author, description, submission_type, contributor_path, url, content, endpoints, tags)
    values (${id}, 'pending', ${String(b.name)}, ${String(b.author)}, ${String(b.description)}, ${sub}, ${cpath},
            ${url}, ${b.content ? String(b.content) : null}, ${b.endpoints ? String(b.endpoints) : null}, ${b.tags ? String(b.tags) : null})
  `;
  return json({ ok: true, id, status: "pending", url,
                note: "Submitted for review. It appears on the public showcase once approved." });
}

async function approve(b: Row) {
  if (!adminOk(b.admin_key)) return json({ error: "Invalid admin key." });
  const db = sql();
  const rows = (await db`select * from showcase where id = ${String(b.id ?? "")}`) as Row[];
  const rec = rows[0] as Row | undefined;
  if (!rec) return json({ error: "No submission with id " + b.id });

  let townResult: Row | null = null;
  if (b.register_in_town !== false) {
    try {
      const sub = String(rec.submission_type);
      const skill = await createSkill({
        name: String(rec.name),
        author: rec.author ? String(rec.author) : null,
        description: rec.description ? String(rec.description) : null,
        endpoints: rec.endpoints ? String(rec.endpoints) : null,
        tags: rec.tags ? String(rec.tags) : null,
        source_type: sub === "writeup" ? "content" : sub === "code" ? "github" : "url",
        source_url: sub === "writeup" ? null : rec.url ? String(rec.url) : null,
        content: sub === "writeup" ? (rec.content ? String(rec.content) : null) : null,
      });
      townResult = { status: 200 };
      if (skill?.id) {
        await db`update showcase set town_registry_id = ${skill.id} where id = ${String(b.id)}`;
      }
    } catch (err) {
      townResult = { error: String(err instanceof Error ? err.message : err).slice(0, 200) };
    }
  }

  await db`update showcase set status = 'approved', approved_at = now() where id = ${String(b.id)}`;
  return json({ ok: true, id: b.id, status: "approved", town_registry: townResult,
                note: "Live on the showcase immediately." });
}

async function reject(b: Row) {
  if (!adminOk(b.admin_key)) return json({ error: "Invalid admin key." });
  const db = sql();
  const rows = (await db`update showcase set status = 'rejected' where id = ${String(b.id ?? "")} returning id`) as Row[];
  if (!rows[0]) return json({ error: "No submission with id " + b.id });
  return json({ ok: true, id: b.id, status: "rejected" });
}
