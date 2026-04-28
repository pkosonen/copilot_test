const https = require('https');

const GRIDLE_URL = "https://residential.gridle.com/api/public/measurements";

function fetchGridle(url, options) {
  return new Promise((resolve, reject) => {
    https.get(url, options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        resolve({ status: res.statusCode, headers: res.headers, body: data });
      });
    }).on('error', (error) => {
      reject(error);
    });
  });
}

module.exports = async (request, response) => {
  response.setHeader('Access-Control-Allow-Origin', '*');
  response.setHeader('Access-Control-Allow-Methods', 'GET');
  response.setHeader('Content-Type', 'application/json');

  if (request.method !== "GET") {
    return response.status(405).json({ error: "Method not allowed" });
  }

  const apiKey = process.env.GRIDLE_API_KEY;
  if (!apiKey) {
    console.error('GRIDLE_API_KEY is not set in environment');
    return response.status(500).json({ error: "Missing GRIDLE_API_KEY environment variable" });
  }

  try {
    const upstream = await fetchGridle(GRIDLE_URL, {
      headers: {
        accept: "application/json",
        "x-api-key": apiKey,
      },
    });

    if (upstream.status >= 400) {
      console.error(`Upstream error: ${upstream.status}`, upstream.body);
      return response.status(upstream.status).json({
        error: `Upstream error: ${upstream.status}`,
        details: upstream.body.substring(0, 200),
      });
    }

    const payload = JSON.parse(upstream.body);
    if (!Array.isArray(payload) || payload.length === 0) {
      console.warn('No measurement data returned');
      return response.status(404).json({ error: "No measurement data returned" });
    }

    return response.status(200).json(payload[payload.length - 1]);
  } catch (error) {
    console.error('Function error:', error);
    return response.status(502).json({
      error: "Failed to fetch Gridle API",
      details: error instanceof Error ? error.message : String(error),
    });
  }
};
