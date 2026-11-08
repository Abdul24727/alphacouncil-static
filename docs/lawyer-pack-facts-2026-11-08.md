# The lawyer pack's three owner facts, checked 2026-11-08

On the owner's instruction ("check it yourself, I log you in wherever needed"), each fact was read in the owner's own
accounts or systems. Everything was read-only: no setting was changed and nothing was sent. No key, password or
personal detail is recorded here.

## Fact 3: where the AI services process the data (pack §5.2 and question (h))

**Source:** the owner's OpenRouter account, read in the owner's Chrome on 2026-11-08: the Activity "Explore" view
for the past month, grouped by model and provider, plus the Privacy and Routing settings.

**What the account shows:**
- **One API key** carried all the month's traffic: 4,160 requests, $49.28.
  - **The site's three configured models:** DeepSeek V3.2 (Copilot), DeepSeek V4 Pro (advisors) and Claude Sonnet
    5.5 (Chair).
  - **Other models on the same key:** Gemini 2.5 Flash, Nano Banana 2 (image generation) and GPT-5.2. These are not
    the site's configured models, so the key appears to serve other work too; the owner can confirm. The traffic is
    not separated by source.
  - **The evaluation runs:** the traffic most likely also includes the paid evaluation runs of 2026-11-06 and
    2026-11-07, which ran on the same server. They are not separated from visitors' requests here.
- **The providers observed on the account, by model** (OpenRouter's "provider", share of the month's spend). This is
  the whole account; no site request was traced to a provider:
  - **Claude Sonnet 5.5:**
    - Azure: $16.00, 32.6%;
    - Claude Platform on AWS: $6.88, 14.0%;
    - Anthropic: $0.15.
  - **DeepSeek V4 Pro:**
    - Relace: $5.51;
    - DigitalOcean: $5.50;
    - Nebius: $2.93;
    - Crusoe: $1.73;
    - Baidu: $1.44;
    - Reka: $0.79;
    - DeepInfra: $0.40;
    - Parasail: $0.02;
    - Cloudflare: under $0.0001.
  - **DeepSeek V3.2:**
    - Phala: $0.50;
    - GMICloud: $0.28;
    - DeepInfra: $0.16;
    - Friendli: $0.08;
    - SiliconFlow: $0.07;
    - Google: $0.007;
    - Venice, AtlasCloud, SambaNova, DigitalOcean and Baidu: each under $0.01.
- **The account's settings** (Privacy and Routing, read 2026-11-08):
  - **Zero Data Retention:** off for every provider group.
  - **Paid endpoints that train on request data:** not allowed. Free endpoints that train: allowed, though the site's
    models are paid.
  - **Allowed or ignored providers, and allowed or blocked model authors:** none set, so every provider may serve
    requests.
  - **Provider sort:** the default, balanced.
  - **Regional routing (EU or US only):** not in use. It needs OpenRouter's Business plan.
- **The site's code** (`api/app/copilot/openai_compat.py`, `host_routing`): when it names preferred providers for
  the Copilot, it sets `allow_fallbacks=True`. That was not established for every production request, so the
  providers above are the ones observed on the account, not confirmed recipients of the site's visitors' data.

**What this establishes for the pack:**
- **Which companies:** on the account, requests for the site's three configured models were served by many
  third-party providers, chosen per request by OpenRouter. No site request was traced.
- **Including companies based in China:** Baidu and SiliconFlow served some DeepSeek requests on the account this
  month. Where a company is based does not show where a request was processed.
- **Not shown:** OpenRouter does not show the country where each request was processed. So the processing location
  stays **not verified**, and requests may be processed outside the Kingdom.
- **What *is* verified:** the providers used on the account, and that nothing on the account limits them by provider
  or region.
- **Options for the owner and the lawyer, not taken here:** limit providers (an allowed or ignored list), turn on
  Zero Data Retention, or use regional routing on the Business plan. Each is a settings change, and the owner's
  decision.

## Fact 2: the hosting provider and the data centre's country (pack §5.2)

**Confirmed: Hostinger, server location Paris, France.**
- **The source:** the owner's Hostinger panel (hPanel), read 2026-11-08 after the owner signed in, VPS Overview.
- **What it shows:**
  - the server `srv1556505.hstgr.cloud`, plan KVM 4, IP 72.60.91.24, running;
  - **"Server location: Paris"**;
  - expiry 2027-05-01, with auto-renewal on;
  - backups weekly.
- **Matches the public records:** reverse DNS `srv1556505.hstgr.cloud`, and RIPE `HOSTINGER-HOSTING`, country FR.
- **One server:** the account lists one VPS.

## Fact 1: the counts as of 2026-11-06 (pack §2)

- **Payments and refunds: two live payments ever, both refunded. The pack says one.**
  - **The source:** the owner's Moyasar dashboard, read 2026-11-08 after the owner signed in. It was the
    **Live Environment**, Payments, with no filter: "Showing 1 to 2".
  - **2026-11-02, 10:24 PM:** 79.00, REFUNDED, "AlphaCouncil Pro, monthly, account …". This is the owner's own
    payment, which the pack describes.
  - **2026-08-12, 01:07 AM:** 79.00, REFUNDED, "AlphaCouncil Pro — monthly". The pack does not mention it. The
    different description format suggests the earlier version of the site, before this rebuild. **The owner, in
    chat, 2026-11-08:** "Mine, a test".
  - **So:** two payments ever, both the owner's own tests, both refunded, and no paying customer.
  - **Not opened:** neither payment's details (card or customer), so nothing personal was read. Dates are as the
    dashboard shows them (day/month/year).
- **Accounts:** **PENDING.** The session's permission check refused a counts-only query of production's accounts
  database again on 2026-11-08, even with the owner's instruction. The owner can run the same query in their own Git
  Bash. It prints counts only, never a name, an email or card data:

  ```bash
  ssh root@alphacouncil.tech "docker exec acp-postgres psql -U acp -d acp_prod -At -F ' ' -c \"SELECT 'accounts', count(*) FROM users UNION ALL SELECT 'accounts_since_2026-11-06', count(*) FROM users WHERE created_at >= '2026-11-06' UNION ALL SELECT 'payments', count(*) FROM billing_payments UNION ALL SELECT 'payment_' || status, count(*) FROM billing_payments GROUP BY status UNION ALL SELECT 'subscription_' || status, count(*) FROM subscriptions GROUP BY status;\""
  ```

  The site's own payment records (`billing_payments`) began with this rebuild. So they should hold the 2026-11-02
  payment, and not the 2026-08-12 one, which Moyasar holds.
