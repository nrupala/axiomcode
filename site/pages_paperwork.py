from build import *

# ---------- paperwork ----------
PW_INTRO = """<section class="block"><div class="wrap"><div class="prose">
<div class="note">These documents govern the AxiomCode service. They are written in plain language and describe process and outcomes, not marketing claims. Material liability and warranty terms should be reviewed by qualified legal counsel before they are relied upon in any dispute.</div>
"""

def pw_page(path, title, desc, body):
    slug = path.strip("/").replace("/", "-") if path != "/paperwork/" else ""
    dl = (f'<p><a href="/paperwork/{slug}.docx" download>Download as Word (.docx)</a></p>' if slug else "")
    page(path, title, desc, PW_INTRO + f'<h1 class="pt">{title}</h1><p class="sub">Last updated: 26 September 2026</p>' + dl + body + "</div></div></section>")

pw_page("/paperwork/", "Trust & paperwork",
        "AxiomCode trust centre: Terms of Service, Privacy Policy, Certificate Policy and CPS, Refund Policy, Service Levels, and Security.",
"""<p class="sub">Everything that governs the service, in one place.</p>
<ul>
<li><a href="/paperwork/terms/">Terms of Service</a> &mdash; the contract for using AxiomCode.</li>
<li><a href="/paperwork/privacy/">Privacy Policy</a> &mdash; what we collect, why, and how long we keep it.</li>
<li><a href="/paperwork/certificate-policy/">Certificate Policy &amp; Certification Practice Statement</a> &mdash; what our certificates mean, how they&rsquo;re issued, renewed, and revoked.</li>
<li><a href="/paperwork/refunds/">Billing, trial &amp; refund policy</a> &mdash; credits, the 10-verification trial, cancellations, refunds.</li>
<li><a href="/paperwork/sla/">Service levels &amp; support</a> &mdash; what uptime and support we commit to.</li>
<li><a href="/paperwork/security/">Security &amp; responsible disclosure</a> &mdash; how we protect the CA, and how to report issues.</li>
</ul>
<p>Downloadable Word copies of each document are linked at the top of each page.</p>
""")

pw_page("/paperwork/terms/", "Terms of Service",
        "AxiomCode Terms of Service: the service, trial terms, credits and payment, acceptable use, certificate reliance, liability limits.",
"""<h2>1. The service</h2>
<p>AxiomCode (&ldquo;we&rdquo;) provides machine-checked verification of software specifications and issues signed certificates recording the verification outcome (&ldquo;certificates&rdquo;). The service is offered through a web interface, a REST API, and an MCP server.</p>
<h2>2. Trial</h2>
<p>New users may run up to 10 trial verifications without payment. Trial verdicts include the verdict and the engine transcript; <strong>trial verdicts never include certificates</strong>. Trial access is rate-limited and may not be resold, shared across accounts to evade the limit, or used to probe the engine adversarially.</p>
<h2>3. Credits and payment</h2>
<p>Paid verification consumes credits (1 credit = US$0.01), metered by engine compute time at the published rate. Credits are purchased in packs through our merchant of record and never expire. Meter records are itemized in your usage report. If you believe a charge is wrong, contact us within 30 days; we correct genuine metering errors with credit.</p>
<h2>4. Acceptable use</h2>
<p>You may not: (a) submit code you have no right to submit; (b) use the service to verify malware, weapons systems, or any unlawful purpose; (c) attempt to extract the CA signing keys, evade metering, or disrupt the service; (d) misrepresent a trial verdict as a certificate, or a revoked/expired certificate as valid.</p>
<h2>5. Your responsibilities</h2>
<p>You are responsible for the specifications you submit: the certificate binds the artifact hash, not your intent. A certificate states that the submitted artifact compiled under the stated toolchain and its proofs checked &mdash; it does not state that your specification is correct, complete, safe, or fit for any purpose. Relying parties must read the <a href="/paperwork/certificate-policy/">Certificate Policy</a> and validate every certificate through the published checker.</p>
<h2>6. Certificates and reliance</h2>
<p>Certificates are factual statements about a verification event, valid for 90 days unless revoked earlier. We publish a revocation list and will revoke certificates affected by toolchain or engine defects. Certificates are not insurance, warranties, or guarantees of software behavior.</p>
<h2>7. Liability</h2>
<p>To the maximum extent permitted by law: the service is provided &ldquo;as is&rdquo;; we disclaim implied warranties of merchantability and fitness for purpose; our aggregate liability for any claim is limited to the amount you paid us in the 12 months preceding the claim. We are not liable for indirect, incidental, or consequential damages, including losses from reliance on a certificate. <em>These terms should be reviewed by qualified legal counsel; insurance backing the CA operation is part of our operating cost and is reflected in pricing.</em></p>
<h2>8. Changes and termination</h2>
<p>We may update these terms with 14 days&rsquo; notice on this page; continued use is acceptance. We may suspend accounts for abuse, non-payment, or unlawful use. You may stop using the service at any time; unused credits remain refundable per the <a href="/paperwork/refunds/">Refund Policy</a>.</p>
<h2>9. Contact</h2>
<p>Questions about these terms: <a href="mailto:hello@axiom-code.com">hello@axiom-code.com</a>.</p>
""")

pw_page("/paperwork/privacy/", "Privacy Policy",
        "AxiomCode Privacy Policy: what data we collect (submitted code, account, metering), why we keep it, retention and deletion, and our no-sale commitment.",
"""<h2>1. What we collect</h2>
<ul>
<li><strong>Submitted artifacts:</strong> the code you ask us to verify, its SHA-256 hash, the verdict, and the engine transcript. We cannot verify without it.</li>
<li><strong>Account data:</strong> email address, API keys, credit balance, and purchase records from our merchant of record.</li>
<li><strong>Metering records:</strong> compute time, credits charged, timestamps &mdash; kept in a tamper-evident log so your bill always reconciles.</li>
<li><strong>Operational logs:</strong> IP addresses and request metadata for abuse prevention, kept briefly.</li>
</ul>
<h2>2. What we never do</h2>
<p>We <strong>never sell your data</strong>. We never use your submitted code to train models. We never disclose your artifacts except as needed to operate the service (e.g., payment processing by our merchant of record) or as required by law.</p>
<h2>3. Why certificates are public-ish</h2>
<p>A certificate is useful precisely because third parties can check it. Certificate contents (artifact hash, verdict, toolchain, serial, validity) and the revocation list are queryable by anyone. The artifact <em>source</em> itself is not published &mdash; only its hash.</p>
<h2>4. Retention and deletion</h2>
<ul>
<li>Artifacts and transcripts: retained while your account is active, to support re-verification and dispute handling; deleted within 90 days of account closure on request.</li>
<li>Metering and purchase records: retained as required for tax and accounting (typically 7 years), in anonymized form where possible after closure.</li>
<li>Operational logs: 30 days.</li>
</ul>
<p>To request deletion or a copy of your data: <a href="mailto:hello@axiom-code.com">hello@axiom-code.com</a>. Some records (revoked certificate entries, tax records) cannot be deleted while the law requires them.</p>
<h2>5. Security</h2>
<p>CA signing keys are held separately from the web service with restricted access; see <a href="/paperwork/security/">Security</a>. No method is perfect; we disclose breaches affecting your data promptly.</p>
""")

pw_page("/paperwork/certificate-policy/", "Certificate Policy & Certification Practice Statement",
        "AxiomCode Certificate Policy and CPS: what certificates assert, validation method, issuance, 90-day validity, renewal, revocation, and incident handling.",
"""<p>This document follows the structure of RFC 3647. It states what AxiomCode certificates mean, how they are issued, and what happens when something goes wrong. <em>It should be reviewed by qualified legal counsel and a PKI auditor before certificates are relied upon in regulated contexts.</em></p>
<h2>1. Introduction</h2>
<p><strong>1.1 Overview.</strong> AxiomCode operates a certification authority (&ldquo;AxiomCode CA&rdquo;) that issues certificates binding a software artifact&rsquo;s hash to a machine-checked verification verdict. Verification-as-evidence, not verification-as-opinion: every certificate carries the evidence needed to re-check it.</p>
<p><strong>1.2 Document name.</strong> AxiomCode Certificate Policy and Certification Practice Statement, version 1.0 (2026-09-26).</p>
<p><strong>1.3 Participants.</strong> The CA (AxiomCode), subscribers (paying customers who request verification), and relying parties (anyone who validates a certificate).</p>
<p><strong>1.4 Certificate usage.</strong> Certificates assert: <em>on the stated date, the AxiomCode engine compiled the artifact with the stated hash under the stated toolchain, and the proof checked.</em> Appropriate uses: audit evidence, procurement deliverables, counterparty assurance. Prohibited reliance: treating a certificate as a warranty of safety, fitness, or intent &mdash; see &sect;9.</p>
<h2>2. Publication</h2>
<p>The CP/CPS, the CA&rsquo;s public verification keys, and the revocation list are published at axiom-code.com and queryable without an account.</p>
<h2>3. Identification and authentication</h2>
<p>Subscribers are identified by account (email + API key). Artifacts are identified by SHA-256 hash computed at submission. No identity vetting of persons is performed: the certificate speaks about the artifact, not the author.</p>
<h2>4. Certificate life-cycle</h2>
<p><strong>4.1 Application.</strong> A paid verification request is a certificate application. Trial requests are never applications &mdash; no certificate can result.</p>
<p><strong>4.2 Issuance.</strong> On a PASSED verdict, the CA signs a certificate containing artifact hash, verdict, toolchain versions, issuer name, unique serial, and a 90-day validity window. FAILED and INCOMPLETE verdicts produce no certificate, ever.</p>
<p><strong>4.3 Validity and renewal.</strong> 90 days from issuance. Renewal is re-verification at the standard credit meter &mdash; there is no shortcut renewal, because the point is fresh evidence.</p>
<p><strong>4.4 Revocation.</strong> The CA revokes a certificate when: (a) a toolchain or engine defect undermines the verdict; (b) the certificate was mis-issued; (c) the subscriber requests it. Revocations are published to the revocation list promptly (target: within 24 hours of the decision) and are permanent.</p>
<p><strong>4.5 Incident handling.</strong> Suspected mis-issuance triggers an internal review; confirmed mis-issuance triggers revocation, a public incident note, and re-verification of affected artifacts at our expense. Mis-issuance is treated as the CA&rsquo;s existential risk.</p>
<h2>5. Operational controls</h2>
<p>Verification runs in isolated, single-use build environments. CA signing keys are segregated from the web/API tier; signing requires the isolated CA service. All issuance, revocation, and metering events are written to a tamper-evident append-only log.</p>
<h2>6. Technical security controls</h2>
<p>Certificates are signed with modern asymmetric signatures (Ed25519); the CA&rsquo;s public keys are published for independent verification. Key generation uses a vetted CSPRNG; private keys are access-controlled and backed up encrypted. Key compromise triggers key rollover, re-issuance of affected certificates, and public disclosure.</p>
<h2>7. Certificate and revocation profiles</h2>
<p>Certificates are signed JSON documents with the fields listed in <a href="/how-it-works/">How it works</a> &sect;3. The revocation list is a signed JSON document listing revoked serials with reason codes and timestamps, updated on every revocation.</p>
<h2>8. Compliance</h2>
<p>We log every issuance and revocation; logs are available to auditors under NDA. Annual self-assessment against this CP/CPS is published in summary form.</p>
<h2>9. Legal matters</h2>
<p>Certificates are factual statements about a verification event, not warranties. Liability is limited as stated in the <a href="/paperwork/terms/">Terms of Service</a>. Subscribers warrant they have the right to submit the artifact. Relying parties must validate certificates through the published checker and revocation list; reliance on an expired or revoked certificate is at the relying party&rsquo;s own risk.</p>
""")

pw_page("/paperwork/refunds/", "Billing, trial & refund policy",
        "AxiomCode billing policy: the 10-verification trial, credit packs, how metering works, cancellations, and the 14-day refund rule for unused credits.",
"""<h2>1. Trial</h2>
<p>Every new email address gets 10 free verifications. Trial verdicts include the verdict and transcript but <strong>never a certificate</strong>. The trial demonstrates the engine; certification is the paid product. One trial per person; creating multiple accounts to harvest trials is abuse and will be suspended.</p>
<h2>2. Credits</h2>
<ul>
<li>1 credit = US$0.01. Packs: Starter $10 (1,000 credits), Growth $50 (5,000), Scale $200 (20,000).</li>
<li>Verification consumes credits by engine compute time at 0.9 credits/second, shown with every verdict and itemized in your usage report.</li>
<li>Credits never expire and are not transferable between accounts.</li>
<li>Payment is processed by our merchant of record (Paddle); we never see or store your card.</li>
</ul>
<h2>3. Refunds</h2>
<p><strong>Unused credits are refundable within 14 days of purchase</strong> &mdash; email <a href="mailto:hello@axiom-code.com">hello@axiom-code.com</a> and we return the unused portion to the original payment method. Credits already consumed by verifications are not refundable: the compute was spent and the evidence delivered. Genuine metering errors are always corrected with credit, no time limit.</p>
<h2>4. Cancellation</h2>
<p>There are no subscriptions to cancel &mdash; credits are prepaid. Stop buying packs whenever you like; your balance, certificates, and history remain available.</p>
<h2>5. Disputes</h2>
<p>Dispute a charge within 30 days with the serial numbers or timestamps involved; we investigate against the tamper-evident meter log, which is the record of truth both sides can inspect.</p>
""")

pw_page("/paperwork/sla/", "Service levels & support",
        "AxiomCode service levels: uptime target, verification queue expectations, support channels and response targets, and what happens when we miss.",
"""<h2>1. Uptime</h2>
<p><strong>Target: 99% monthly availability</strong> for the API and certificate checker, excluding scheduled maintenance (announced 48h ahead) and upstream outages. The static site and published revocation list are served from the edge and targeted higher, but the commitment we make is 99% on the API.</p>
<h2>2. Verification queue</h2>
<p>Verifications normally start within 60 seconds. At high load, paid verifications queue ahead of trial verifications, and Scale customers queue ahead of others. Engine time per call is capped; very large artifacts may be asked to split submissions.</p>
<h2>3. Support</h2>
<ul>
<li><strong>Email:</strong> <a href="mailto:hello@axiom-code.com">hello@axiom-code.com</a> &mdash; target first response 1 business day.</li>
<li><strong>Mis-issuance / revocation issues:</strong> treated as critical; target acknowledgment 4 business hours.</li>
<li><strong>Docs and status:</strong> this site&rsquo;s documentation; a status page ships with the production rollout.</li>
</ul>
<h2>4. Remedies</h2>
<p>If monthly API availability falls below 99%, affected paying customers receive a 10% credit rebate for the month, applied automatically. This is our sole remedy for downtime and is without prejudice to the liability limits in the <a href="/paperwork/terms/">Terms</a>.</p>
""")

pw_page("/paperwork/security/", "Security & responsible disclosure",
        "AxiomCode security: how the CA and signing keys are protected, what we ask of researchers, and how to report vulnerabilities.",
"""<h2>1. How we protect the CA</h2>
<ul>
<li><strong>Key segregation:</strong> CA signing keys live in an isolated service, separate from the web and API tiers. The public internet never touches the signer.</li>
<li><strong>Least privilege:</strong> few humans can touch the CA; every touch is logged.</li>
<li><strong>Tamper-evident logs:</strong> issuance, revocation, and metering are append-only and hash-chained. If the log doesn&rsquo;t reconcile, we treat it as an incident.</li>
<li><strong>Isolated builds:</strong> every verification runs in a single-use environment; artifacts can&rsquo;t see each other or the host.</li>
<li><strong>Dependency hygiene:</strong> the Lean toolchain is pinned; upgrades are tested against the regression suite before they touch production verdicts.</li>
</ul>
<h2>2. Responsible disclosure</h2>
<p>Found a vulnerability? Email <a href="mailto:security@axiom-code.com">security@axiom-code.com</a> with the details and a way to reach you. We ask for a reasonable window (90 days) before public disclosure so we can fix, revoke affected certificates if needed, and publish an incident note. We commit to acknowledging within 2 business days and keeping you updated.</p>
<h2>3. Scope</h2>
<p>In scope: the API, the MCP server, the certificate checker, the CA issuance path, and this site. Out of scope: third-party services (Paddle, Cloudflare), social engineering, and physical attacks. Please don&rsquo;t disrupt the service or access other customers&rsquo; data while researching.</p>
<h2>4. What we won&rsquo;t do</h2>
<p>We won&rsquo;t threaten researchers who follow this policy, and we won&rsquo;t ask law enforcement to chill good-faith research. If you&rsquo;re unsure whether something is in scope, ask first.</p>
""")
