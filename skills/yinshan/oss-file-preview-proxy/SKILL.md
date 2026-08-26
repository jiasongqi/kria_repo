---
name: oss-file-preview-proxy
description: >-
  Business-side proxy streaming for Aliyun OSS file preview/download, with HTTP
  cache validation (ETag + versioned Cache-Control), instant publish-invalidation,
  and a dedicated async executor with graceful overload handling. Use when OSS
  signed URLs fail externally, browsers download instead of previewing files,
  response-content-type is rejected by Aliyun, implementing file-config
  batch/preview APIs (ys-config pattern), or asked to reduce repeated OSS reads
  for a preview endpoint.
---

# OSS File Preview Proxy

## When to use

- OSS signed URL works internally but not on public network (`-internal` endpoint)
- Browser downloads HTML/PDF instead of rendering
- Aliyun error: `Can not override response header on content-type` (0017-00000902)
- Business APIs return `downloadUrl` for App/H5 to open files (e.g. privacy policy)
- Preview endpoint re-downloads from OSS on every single request and you need caching
- Async/streaming controller needs a dedicated thread pool with saturation handling

## Decision guide

| File type | Approach |
|-----------|----------|
| Public (privacy policy, terms) | Business **preview proxy** (anonymous OK) + HTTP cache validators |
| Private (e-sign contracts, ID docs) | Auth + short-lived OSS signed URL or expiring token — **not** anonymous permanent preview |

## Pattern A — Business preview proxy (preferred for public preview)

Do **not** return OSS signed URLs to clients for preview. The business service streams
OSS bytes through itself so it can control `Content-Type` / `Content-Disposition` and
keep OSS endpoints off the public network.

1. Batch/latest metadata APIs set `downloadUrl` to the business preview endpoint,
   carrying enough info to validate cache freshness (see Pattern B):
   `https://{business-host}/api/.../preview?fileKey={key}&locale={locale}&v={versionNo}&rev={revisionHash}`
2. Preview handler:
   - Resolve `fileKey` (+ scope/locale) → cached `FileConfigSnapshot` (filePath, contentType,
     versionNo, fileSize) — **do not** query OSS metadata per request; keep that in your
     existing DB/Redis/Caffeine snapshot cache.
   - Stream `downloadFile(filePath)` from OSS via `StreamingResponseBody` + `transferTo`
     (never load the whole file into memory).
   - Response headers: `Content-Type` (resolved mime, else guess from filename),
     `Content-Disposition: inline`, `Content-Length` when known.
3. Build the absolute preview URL carefully:
   - Prefer config `config.public-base-url=https://...` (or env)
   - Else use request host + force `https` for non-local (gateway SSL termination often
     yields `http://`, which Android cleartext policy blocks)
   - Honor `X-Forwarded-Proto` when present

This is a **proxy**, not a short link: the client never hits OSS directly; the server
fetches and forwards every time the cache layer below doesn't intercept the request.

## Pattern B — HTTP cache validation (prevents re-hitting OSS on every request)

Without cache headers, every preview request — even a page refresh — re-downloads from
OSS through the proxy. Add ETag + `Cache-Control`, computed from `filePath + versionNo`
(no need to hash file bytes):

```java
public static String revision(String filePath, Integer versionNo) {
    String source = filePath + ":" + versionNo;
    byte[] digest = MessageDigest.getInstance("SHA-256").digest(source.getBytes(UTF_8));
    return HexFormat.of().formatHex(digest).substring(0, 32); // opaque, doesn't leak filePath
}
public static String etag(String filePath, Integer versionNo) {
    return "\"" + revision(filePath, versionNo) + "\"";
}
```

Metadata endpoints append `v={versionNo}&rev={revision}` to the generated `downloadUrl`
(see `FileConfigResAssembler.appendPreviewQueryParams`). The preview handler then:

1. **Version/revision mismatch check first** — always look up the **current** snapshot for
   `fileKey` (not a historical one by version). If the request carries `v`/`rev` and either
   doesn't match the current snapshot, the link is stale (file was republished) → return
   `410 Gone` with `Cache-Control: no-store`. Do **not** silently serve old or new content —
   force the client to re-fetch metadata for a fresh URL.
2. **ETag / conditional GET** — compute `etag = sha256(filePath, versionNo)`. If the
   incoming `If-None-Match` matches (support multiple comma-separated values, `*`, and
   `W/` weak prefix), return `304 Not Modified` with the same `Cache-Control` and **skip
   the OSS download entirely**.
3. **Cache-Control differs by whether the link is versioned**:
   - Versioned (`v`+`rev` present and valid): `public, max-age=86400, immutable` — safe for
     CDN/browser to cache a full day and skip revalidation, because a new version always
     gets a new URL.
   - Legacy/unversioned (no `v`/`rev`, e.g. old cached client): `private, max-age=300` +
     `Vary: X-Locale, Accept-Language` (locale affects which file variant is served).
4. Only a genuine cache miss (no matching ETag, first request, or after cache expiry)
   actually calls `fileStoragePort.downloadFile(...)` and streams from OSS.

### Publish-time cache invalidation (keep metadata fresh, not stale)

The **metadata** cache (which fileKey → which version/filePath) must invalidate
immediately on publish, or clients keep getting old `downloadUrl`s long after a new
version exists. Use a version-counter-based cache (not per-key deletes):

```java
@TransactionalEventListener
public void handleFileVersionPublished(FileVersionPublishedEvent event) {
    fileConfigCacheService.incrementFileVersion(scopeKey); // bumps a Redis counter
}
```

Cache keys embed this counter (`f:{scopeKey}:{fileKey}:{locale}:{version}`), so bumping it
makes all old keys unreachable instantly — no manual per-key eviction, no TTL wait. The
very next metadata call reloads from DB and returns a `downloadUrl` with the new `v`/`rev`.

### Client integration requirement

Clients (App/H5) must **re-fetch the metadata endpoint** to get a fresh `downloadUrl`
before rendering — never persist/hardcode the preview URL long-term. If a client does
cache the URL and it goes stale, the proxy returns `410 Gone`; the client should treat
that as "refetch metadata and retry", not a hard failure.

## Pattern C — Dedicated async executor for streaming controllers

`StreamingResponseBody` / `Callable` / `DeferredResult` run on Spring MVC's async task
executor, not the request thread. Give this its own bounded pool, don't reuse
`@Async`'s default `SimpleAsyncTaskExecutor` (unbounded) or block the app's other work:

```java
@Bean(name = "filePreviewThreadPoolExecutor")
public ContextAwareThreadPoolExecutor filePreviewThreadPoolExecutor(FilePreviewAsyncProperties p) {
    BlockingQueue<Runnable> queue = p.getQueueCapacity() > 0
        ? new ArrayBlockingQueue<>(p.getQueueCapacity())
        : new SynchronousQueue<>(); // queueCapacity<=0 => direct handoff, no queueing
    ContextAwareThreadPoolExecutor executor = new ContextAwareThreadPoolExecutor(
        p.getCorePoolSize(), p.getMaxPoolSize(), p.getKeepAliveSeconds(), SECONDS,
        queue, ThreadPoolUtil.buildThreadFactory("file-preview"),
        new ThreadPoolExecutor.AbortPolicy());
    executor.allowCoreThreadTimeOut(true);
    return executor;
}

@Bean(name = "filePreviewTaskExecutor")
public AsyncTaskExecutor filePreviewTaskExecutor(
        @Qualifier("filePreviewThreadPoolExecutor") ContextAwareThreadPoolExecutor executor) {
    return new ConcurrentTaskExecutor(executor); // adapts raw Executor to Spring's AsyncTaskExecutor
}

@Bean
public WebMvcConfigurer filePreviewAsyncWebMvcConfigurer(
        @Qualifier("filePreviewTaskExecutor") AsyncTaskExecutor taskExecutor, FilePreviewAsyncProperties p) {
    return new WebMvcConfigurer() {
        @Override public void configureAsyncSupport(AsyncSupportConfigurer c) {
            c.setTaskExecutor(taskExecutor);
            c.setDefaultTimeout(p.getRequestTimeoutMillis());
        }
    };
}
```

Key points:

- **`ContextAwareThreadPoolExecutor`** (`com.ys.frame.common.utils.thread`, already in
  `frame-common`) instead of plain `ThreadPoolTaskExecutor`/`ThreadPoolExecutor`: it
  auto-wraps submitted tasks to snapshot/restore MDC + SkyWalking trace context on the
  worker thread, so log lines produced while streaming still carry the request's
  traceId. It does **not** propagate arbitrary custom `ThreadLocal`s (e.g. a user-context
  holder) — only MDC/trace. Add a custom `TaskDecorator` if you need more.
- Externalize `corePoolSize/maxPoolSize/queueCapacity/keepAliveSeconds/requestTimeoutMillis
  /shutdownAwaitSeconds` via `@ConfigurationProperties` with `@Min`/`@Max`/`@AssertTrue`
  cross-validation (e.g. `maxPoolSize >= corePoolSize`) — don't hardcode.
- Raw `ThreadPoolExecutor` has no Spring lifecycle shutdown hooks; wire one explicitly:
  `ThreadPoolUtil.gracefulShutdown(executor, shutdownAwaitSeconds, SECONDS)` in a
  `DisposableBean` (shutdown → wait → shutdownNow if still not terminated).
- **Saturation handling**: when the pool + queue are full, Spring throws
  `TaskRejectedException`. Map it in the global exception handler to `503 Service
  Unavailable` instead of a generic 500, so overload degrades gracefully:

  ```java
  @ExceptionHandler(TaskRejectedException.class)
  @ResponseStatus(HttpStatus.SERVICE_UNAVAILABLE)
  public Response<?> handleTaskRejected(TaskRejectedException e) {
      return Response.failed(503, "File preview service is busy, please retry later");
  }
  ```

### Testing this executor without CGLIB pitfalls

If you unit-test the saturation-handling exception mapping with a standalone
`MockMvcBuilders.standaloneSetup(new SomeController())`, and that controller is a nested
test class, do **not** mark it `private` and do **not** rely on it never being scanned:
if the app's `@ComponentScan` base package covers the test's package (common when scan
base is broad, e.g. `com.ys.config`), any unrelated test that boots the **full** Spring
context will pick up an `@RestController`-annotated nested class as a real bean and try
to CGLIB-proxy it. A `private` nested class's implicit constructor is also `private`
(JLS 8.8.9), which CGLIB can't see → `No visible constructors` → that unrelated test's
context fails to load. Fix: keep the nested test controller package-private (drop
`private`), not `@RequestMapping`-only (breaks `standaloneSetup` handler detection).

## Pattern D — OSS signed URL for public access (admin download / when proxy not used)

```java
String url = ossClient.generatePresignedUrl(request).toString();
// Internal endpoint → public endpoint; keep query string intact
return url.replace("-internal.aliyuncs.com", ".aliyuncs.com");
```

Optional: set response `Content-Disposition: inline` on the signed request.

**Never** set response `Content-Type` override on signed URLs — Aliyun may reject with
InvalidRequest.

On **upload**, set object metadata correctly:

- `Content-Type` (e.g. `text/html`, `application/pdf`)
- `Content-Disposition: inline` (filename optional)

## Anti-patterns

- Returning OSS signed URLs directly for public preview (Pattern A should proxy instead)
- No cache headers at all (`CacheControl.noStore()`) on a proxy endpoint — every view
  re-downloads from OSS; the fix is Pattern B, not disabling the proxy
- Deriving the versioned Cache-Control lifetime (`immutable`) from anything other than an
  actual content-bound revision (`filePath + versionNo`) — otherwise stale content can be
  cached for a full day
- Silently serving old content when `v`/`rev` doesn't match current — return `410 Gone`
  instead so clients know to refetch
- Reusing the default unbounded `SimpleAsyncTaskExecutor` for streaming controllers
- `openDomain + url.getFile()` with trailing-slash mistakes (prefer `-internal` string
  replace for OSS hosts)
- Adding `response-content-type` to signed URLs
- Using anonymous permanent preview for e-sign / PII files
- Returning `http://` public preview URLs to Android clients

## Implementation checklist

- [ ] Public preview: `downloadUrl` → business `/preview?fileKey=&v=&rev=`
- [ ] Preview streams with correct `Content-Type` + `inline`, without buffering whole file
- [ ] ETag (`sha256(filePath+versionNo)`) + conditional `304` support
- [ ] Versioned links: `Cache-Control: public, max-age=86400, immutable`
- [ ] Unversioned/legacy links: `Cache-Control: private, max-age=300` + `Vary`
- [ ] Stale `v`/`rev` → `410 Gone`, `Cache-Control: no-store`
- [ ] Publish event bumps a version counter to invalidate metadata cache instantly
- [ ] Dedicated bounded async executor for the MVC async support, not the default one
- [ ] Executor uses `ContextAwareThreadPoolExecutor` (MDC/trace propagation)
- [ ] Executor params externalized + validated; graceful shutdown wired explicitly
- [ ] `TaskRejectedException` → `503`, not a generic 500
- [ ] Preview URL is `https://` (or `config.public-base-url` set)
- [ ] OSS public access: replace `-internal.aliyuncs.com` → `.aliyuncs.com`
- [ ] No `response-content-type` on signed URLs
- [ ] Private files: auth + short TTL, not anonymous proxy

## Reference (ys-config-business)

- Metadata/URL building: `FileConfigResAssembler.buildBusinessPreviewUrl` /
  `appendPreviewQueryParams`
- Cache token: `FilePreviewCacheToken.revision` / `.etag`
- Preview response building (410/304/200 + headers): `FilePreviewResponseFactory.build`
- Query orchestration: `ConfigBusinessQueryAppService.buildFilePreviewResponse`
- Metadata cache (Caffeine L1 + Redis L2, version-counter invalidation):
  `FileConfigCacheService`
- Publish → cache invalidation: `CacheInvalidationListener.handleFileVersionPublished`
- Async executor + MVC wiring: `FilePreviewAsyncConfiguration`,
  `FilePreviewAsyncProperties`
- Saturation → 503: `GlobalExceptionHandler.handleTaskRejected`
- Endpoint: `GET /api/v1/config/file-config/preview`
- OSS adapter: `AliOssStorageAdapter.toPublicUrl` (`-internal` replace)
- Config: `config.public-base-url` / `CONFIG_PUBLIC_BASE_URL`,
  `config.file-preview.async.*`

## Future direction (not yet implemented)

There's a plan (`ys-frame-parent/.cursor/plans/oss_preview_common_72f38030.plan.md`) to
move this proxy into a shared `frame-oss` module (`OssPreviewController` +
HMAC-signed short-lived tokens instead of `fileKey`+`v`+`rev`, default-off via
`ys.oss.preview.enabled`). All todos in that plan are still `pending` — the patterns
above describe what's actually live today in `ys-config-business`.
