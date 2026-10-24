import http from 'k6/http';
import { check, sleep } from 'k6';

// Thora load: ramp up, hold, ramp down. Isse real jaisa usage pattern banta hai.
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
