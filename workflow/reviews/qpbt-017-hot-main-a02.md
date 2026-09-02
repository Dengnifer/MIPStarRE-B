# QPBT-017 hot-main cache readiness A02

## Scope

- Main snapshot: `4a6683795a71712d6a5c52b7539c2f532fd39f71`
- Stable session: `i017-builder-a02-hot-main-retry`
- External task path: `/root/i017_builder_a02_hot_main_retry`
- Role: singleton hot-main builder
- Outcome: cache hit; no compilation was required

## Authenticated cache result

- Cache key: `303d4b07cd0c9ccc9b83d83f69da6e35794fa2a3bdcc5ee18eceb3e6dc0f2624`
- Recipe: `qpbt-hot-main`, schema 3, version 7
- Result: `hit`
- Builds: `0`
- Lock wait: `0.0 s`
- Command elapsed: `0.001052 s`
- Inventory: 124,925 files; 4,147 directories; 3 symlinks; 10,097,592,794 bytes
- Inventory hash: `595e4ea212a73b21766933c3ef34108d15eb126c6859d0abfe07120bf45ae637`

The documented MIPStarRE archive path contained a naming typo (`FJmb6mA`);
the authenticated archive at `FJmb6mA8` was used after hash verification. No
tracked files, workflow state, research metrics, GitHub objects, credentials,
or shared writable build output were changed by the builder.

## Validation

The filesystem lock elected one builder and the atomically published cache was
reused without a duplicate build. Token usage was unavailable from the
collaboration backend and is recorded as JSON `null` in the session metric.
