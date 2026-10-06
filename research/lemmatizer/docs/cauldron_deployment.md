# Cauldron deployment feasibility

Audited 2026-10-06. No deployment, shared-index write, branch push, or secret read
was performed. Local sources: Sefaria-Project experimental branch based on
78e6ceaa2; cauldrons aed3ac183 (2026-09-17); infrastructure 8d1f0d9 (2026-08-23).
Wiki consulted: Cauldron lifecycle, Celery Task Infrastructure, Development Cluster
Topology, and cauldrons/CLAUDE.md. Local repository versions are not proof of live
cluster state. A read-only service lookup with the explicit dev context failed:
Kubernetes rejected current credentials. Live services, installed chart/plugin
versions, available capacity, and Elasticsearch permissions remain unverified.

## Conclusion

Feasible with an application adaptation and packaging work, not just environment
variable changes. Reuse the existing dev Elasticsearch and Redis/Sentinel. Deploy
one Cauldron web app and its own Celery task worker, initially CPU/concurrency 1.
Keep ordinary site search separate from the experimental endpoint.

## Proposed request flow

Browser -> Cauldron Django -> Celery task on <cauldron>-tasks -> Shoshan + dedicated
index on shared dev Elasticsearch -> Redis result backend -> Django polling API.

The existing page already submits and polls jobs, so its interaction need not
change. Replace localhost HTTP forwarding and in-memory futures with a named
Celery task and AsyncResult. Reuse the same comparison engine inside the task;
lazily initialize once per worker child, after fork. Avoid loading model weights
in gunicorn or the Celery parent. Enable task discovery, bound runtimes, limit
outstanding work, expire results, and associate job IDs with requesting sessions.
The existing app sets result_expires=1800 (30 minutes).

## Existing deployment support, checked against code

- cauldrons/create-cauldron.sh supports --tasks. It configures Sentinel at
  redis-headless.redis.svc.cluster.local:26379, master mymaster, broker DB 2 and
  result backend DB 3. Credentials are referenced Kubernetes secrets, not literal
  values. This is distinct from the per-Cauldron Redis used for application caches.
- helm-chart/sefaria/templates/_helpers.tpl derives the internal queue as
  <deployEnv>-tasks. rollout/task.yaml consumes only that queue, concurrency 1.
  Do not send this experiment to the shared llm-default-llm queue.
- The stock task pod uses the WEB image, not a separately configurable task image.
  Simplest POC packaging: add pinned CPU ML dependencies and immutable model/data
  artifacts to the branch image, but only initialize them in the task process.
  Cleaner smaller web images require a chart/CI extension for a separate worker
  image and artifact mounting/downloading. Do not download models per search.
- tasks.localsettings and web.localsettings support arbitrary environment values;
  generated local-settings-file.yaml must also explicitly read new settings.
  The ignored laptop local_settings.py is not deployed.
- Default task resources are 500m CPU/2Gi requested, 1 CPU/4Gi limited. Measure full
  Django+model RSS and CPU latency before choosing actual limits. Keep one warm
  task replica for the demo (KEDA minReplicas=1 or disable task scaling) to avoid
  repeated model startup. Do not infer live capacity from defaults.
- Creating a Cauldron writes HelmRelease/image policies and commits to cauldrons
  main, which triggers Flux. Even --dryrun creates/pushes a review branch; it is
  not a read-only command. Do not execute for an audit.
- Branch images are built by the Sefaria-Project PR workflow. A local uncommitted
  branch cannot be deployed. Confirm a published branch image and matching assets.
  If chart templates change, publish/pin a branch chart release explicitly;
  tracking branch application images alone does not use its chart changes.

## Elasticsearch plan

Infrastructure's ECK manifest specifies Elasticsearch 8.8.0 plus analysis-icu and
both Sefaria Hebrew analyzer plugins v1.1.6, matching the local Docker experiment.
Chart defaults use SEARCH_HOST=elasticsearch-es-default.elasticsearch. Verify the
actual HTTP service (ECK service names may differ), plugins, auth and health live
before importing. Do not treat the creation script's legacy SEARCH_ADMIN URL as
an independently verified endpoint.

Create a NEW, uniquely named index, e.g. lemma-poc-<cauldron>-tanakh-rashi-mishnah-v1.
Import the existing documents and saved lemma strings (55,589 documents), preserving
mapping, analyzers, pagesheetrank, provenance, and ready status. No Shoshan corpus
rerun is needed. Use an explicit importer target and index allowlist with existing
index refusal; the present offline loader correctly refuses nonlocal destinations
and must not be globally weakened. Separate import credentials from read-only
query credentials where supported. Verify count, hashes, and representative queries.
Do not change shared text/sheet/entity aliases or enable a global reindex job.

Add dedicated endpoint settings, e.g. LEMMA_SEARCH_INDEX and connection configuration,
resolved server-side. Do not repoint global SEARCH_INDEX_NAME_TEXT to this partial
corpus: ordinary search and index-on-save paths could interfere. The generated
cluster settings currently set SEARCH_INDEX_ON_SAVE=True; this reinforces the need
for separate experiment settings. Clients must not select arbitrary indexes.

## Artifacts and platform

Current local footprint: model tree ~1.0 GB, lemma JSONL ~280 MB, source corpus
JSONL ~58 MB; indexed primary store ~55.1 MB. Redis holds jobs/results only, not
weights or the full corpus. Result word tooltips and spelling expansion need the
verified annotation export at a stable container path. The current runtime imports
code from a sibling Sefaria-Data checkout and resolves local model paths: package
those exact modules/artifacts deliberately instead of assuming that checkout exists.

CPU smoke test on this Mac (not the cluster, not x86 Linux): model load 6.79 s;
first query 0.517 s; subsequent short-query inference 0.026 and 0.025 s. This supports
trying CPU for a low-traffic demo. Apple MPS is unavailable on Linux; validate pinned
Linux wheels, dependency compatibility, full-process memory, and query output parity.
GPU is optional later, not a prerequisite established by this audit.

## Required web changes

Current reader/lemma_search.py deliberately returns 404 unless DEBUG, an experiment
flag, and a loopback client all hold. Replace that local-only guard with an explicit
dev feature flag plus authenticated staff/approved tester access. Keep DEBUG off;
do not simply remove access checks on a public Cauldron. Preserve CSRF protection
and prevent caching of job responses. Replace the localhost:19201 dependency with
Celery dispatch/polling. Keep this under /experimental/lemma-search/.

## Suggested sequence

1. Package reproducible CPU runtime/artifacts and port jobs to Celery; add separate
   endpoint settings and tester access. Test Redis/Sentinel dispatch and expiry.
2. Build/test Linux image, measure memory/latency, and verify model outputs match
   local expectations. Select worker resources and keep one warm worker.
3. Restore dev Kubernetes access; read-only check ES service/plugins/auth/capacity,
   Redis/Sentinel, and installed chart support.
4. Prepare a reviewable Cauldron spec with --tasks-equivalent settings and the
   published experiment branch image; pin a chart if templates were changed.
5. Import only the dedicated index; verify count/provenance. Deploy the reviewed
   spec and test through the HTTPS browser endpoint with a teammate account.
6. Compare baseline, lemma, and spelling-expanded results on the same corpus.
   Arrange explicit cleanup for the dedicated ES index and artifacts; Cauldron
   removal does not inherently remove a custom shared-cluster index.
