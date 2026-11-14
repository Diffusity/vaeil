# T4 free-plan verification — 10 November 2026

Official sources: [Render Free](https://render.com/docs/free) and [Neon plans](https://neon.com/docs/introduction/plans).

Render Free provides 750 instance hours per workspace per month, sleeps after 15 idle minutes, and displays a platform loading page during wake-up (documented as about a minute). Files are ephemeral; persistent disks are unavailable. Exhausted hours suspend services. With no payment method, exhausted bandwidth suspends services and exhausted pipeline minutes disable new builds. An additional high outbound-traffic threshold can suspend a service. Hobby/demo use is supported; production reliability is not promised. Workspace quotas are shared with any other services.

Neon Free currently lists 100 CU-hours per project per month, 1 GB storage per project (20 GB account total), 5 GB public transfer per project per month, five-minute idle suspend and unlimited organization members. Exhausted compute/transfer suspends compute until reset or upgrade; operations increasing storage fail at the storage cap. Quota exhaustion does not delete data. These are current public limits, replacing older storage figures; no paid upgrade is approved.

PR21 head83852d1 passed Windows, Linux container and secret-scanning CI (run42797767880). The constrained image smoke passed anonymous JSON, HTML/assets, health and database-unavailable behaviour, plus the non-root check. One memory sample was34.16MiB/512MiB. This is CI evidence, not live Render RAM or successful Neon TLS evidence.

Live deployment, real database readiness, sleep/wake, outage and continuity checks remain pending. Credentials and private account/resource metadata are intentionally absent.
