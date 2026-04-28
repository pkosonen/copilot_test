const GRIDLE_URL = "https://residential.gridle.com/api/public/measurements";

export default async function handler(request, response) {
  if (request.method !== "GET") {
    response.setHeader("Allow", "GET");
    return response.status(405).json({ error: "Method not allowed" });
  }

  const apiKey = process.env.GRIDLE_API_KEY;
  if (!apiKey) {
    return response.status(500).json({ error: "Missing GRIDLE_API_KEY" });
  }

  try {
    const upstream = await fetch(GRIDLE_URL, {
      headers: {
        accept: "application/json",
        "x-api-key": apiKey,
      },
    });

    if (!upstream.ok) {
      const text = await upstream.text();
      return response.status(upstream.status).json({
        error: `Upstream error: ${upstream.status}`,
        details: text,
      });
    }

    const payload = await upstream.json();
    if (!Array.isArray(payload) || payload.length === 0) {
      return response.status(404).json({ error: "No measurement data returned" });
    }

    return response.status(200).json(payload[payload.length - 1]);
  } catch (error) {
    return response.status(502).json({
      error: "Failed to fetch Gridle API",
      details: error instanceof Error ? error.message : String(error),
    });
  }
}
