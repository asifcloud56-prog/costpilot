import http from 'k6/http';
import { check, sleep } from 'k6';

// Gentle load: 0 to 5 users, then gradually up to 20, then back to 0.
export const options = {
  stages: [
    { duration: '1m', target: 5 },
    { duration: '5m', target: 20 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<500'],
  },
};

const BASE = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  const res = http.get(`${BASE}/work`);
  check(res, { 'status 200': (r) => r.status === 200 });
  sleep(1);
}
