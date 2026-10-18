/* EasyCalc service worker
 * - 페이지(HTML): 네트워크 우선. 인터넷이 되면 항상 최신 요율로, 안 되면 저장해 둔 페이지로 열림
 * - 아이콘·글꼴: 저장본 우선 (빠르게)
 * VERSION은 build.py가 빌드 날짜로 바꿔 넣습니다. 바뀌면 이전 저장본은 자동 삭제됩니다.
 */
const VERSION = '__VERSION__';
const CACHE = 'easycalc-' + VERSION;
const PRECACHE = __PRECACHE__;

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k.startsWith('easycalc-') && k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// 페이지가 자기 언어의 계산기 주소를 알려주면 미리 저장 (오프라인 대비)
self.addEventListener('message', e => {
  const urls = e.data && e.data.precache;
  if (Array.isArray(urls)) caches.open(CACHE).then(c => c.addAll(urls.filter(u => typeof u === 'string' && u.startsWith('/')))).catch(() => {});
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const sameOrigin = url.origin === self.location.origin;
  const isFont = url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com';
  if (!sameOrigin && !isFont) return;           // 광고·분석 스크립트 등은 건드리지 않음

  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req).then(res => {
        if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
        return res;
      }).catch(() => caches.match(req).then(r => {
        if (r) return r;
        const seg = url.pathname.split('/')[1];      // 언어 폴더(/en/ 등)의 첫 화면으로 대신 열기
        return caches.match('/' + seg + '/').then(x => x || caches.match('/'));
      }))
    );
    return;
  }

  e.respondWith(
    caches.match(req).then(hit => {
      const net = fetch(req).then(res => {
        if (res.ok || res.type === 'opaque') { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
        return res;
      }).catch(() => hit);
      return hit || net;
    })
  );
});
