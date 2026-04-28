const https = require('https');
const url = require('url');

const GRIDLE_URL = "https://residential.gridle.com/api/public/measurements";

function fetchGridle(urlString, options) {
  return new Promise((resolve, reject) => {
    const urlObj = new url.URL(urlString);
    const requestOptions = {
      hostname: urlObj.hostname,
      path: urlObj.pathname + urlObj.search,
      method: 'GET',
      headers: options.headers || {},
    };

    https.request(requestOptions, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          body: data,
        });
      });
    }).on('error', (error) => {
      reject(error);
    }).end();
  });
}

module.exports = async (request, response) => {
  // CORS headers
  response.setHeader('Access-Control-Allow-Origin', '*');
  response.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  response.setHeader('Content-Type', 'application/json');

  if (request.method === 'OPTIONS') {
    return response.status(200).end();
  }

  if (request.method !== 'GET') {
    return response.status(405).json({ error: 'Method not allowed' });
  }

  const apiKey = process.env.GRIDLE_API_KEY;
  if (!apiKey) {
    console.error('[api/latest] GRIDLE_API_KEY not found in environment');
    return response.status(500).json({
      error: 'Server configuration error',
      message: 'GRIDLE_API_KEY not set',
    });
  }

  try {
    console.log('[api/latest] Fetching from Gridle API...');
    const upstream = await fetchGridle(GRIDLE_URL, {
      headers: {
        accept: 'application/json',
        'x-api-key': apiKey,
      },
    });

    if (upstream.status >= 400) {
      console.error(`[api/latest] Upstream error: ${upstream.status}`);
      return response.status(upstream.status).json({
        error: `Upstream API error: ${upstream.status}`,
      });
    }

    const payload = JSON.parse(upstream.body);
    if (!Array.isArray(payload) || payload.length === 0) {
      console.warn('[api/latest] No data returned from Gridle');
      return response.status(404).json({ error: 'No measurement data' });
    }

    console.log('[api/latest] Success');
    return response.status(200).json(payload[payload.length - 1]);
  } catch (error) {
    console.error('[api/latest] Error:', error.message);
    return response.status(502).json({
      error: 'Failed to fetch data',
      message: error.message,
    });
  }
};
