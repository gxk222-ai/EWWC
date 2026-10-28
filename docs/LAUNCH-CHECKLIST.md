# Launch checklist

Work through every item before setting `review_mode` to `false`. The production build fails while unverified placeholders remain, but the items below also cover things a build cannot check.

## 1. Facts and approvals (owner: Vanessa Ross)

- [ ] **Contact email.** Confirm `vross@ewroldwidesconsulting.com`. The domain may be misspelled ("ewroldwides"), and a public résumé references a different domain. Update `content/site.json` and set `verified: true`. Do not substitute an address without confirmation.
- [ ] **Production domain.** Set `site_url` in `content/site.json` (used for canonical URLs, sitemap, social images and structured data).
- [ ] **Founder title.** Confirm the full title (for example "Founder & CEO").
- [ ] **Founder portrait.** Supply or approve a professional portrait; replace the monogram placeholders on Home and Founder pages.
- [ ] **Founding year.** Confirm the actual founding or incorporation year. Do not assume 2020.
- [ ] **Founder biography and professional profile.** Verify every statement against Vanessa's LinkedIn profile and with Vanessa. Prior-employer achievements (such as large-scale data migration and business-case development) must be described as her individual experience, not E Worldwide Consulting projects.
- [ ] **Certifications and education.** Add verified items or remove the card.
- [ ] **Founder story timeline.** Confirm dates, sequence and real events for each chapter.
- [ ] **Leadership philosophy.** Approve the wording, or replace it with attributed statements from Vanessa.
- [ ] **Founder letter.** Vanessa reviews and approves the letter before it is published as her words.
- [ ] **Milestones.** Add confirmed milestones (founding, first major client, capability expansion, US and South African growth, partnerships).

## 2. Company claims

- [ ] **Case studies.** Publish only approved projects. Named clients need written permission; anonymized ones need company approval. Every outcome needs a verifiable source. Remove or keep placeholder slots out of production (they are hidden automatically when review mode is off).
- [ ] **Team.** Only real people with approved name, title, bio and photo. No proposed roles shown as employees.
- [ ] **Operating model.** Describe accurately how delivery is staffed (employees, contractors, partners, distributed specialists) on the Team page.
- [ ] **Industries.** Confirm which industries have actual client experience; keep the rest framed as target industries.
- [ ] **Cloud platforms.** Confirm which platforms (AWS, Google Cloud, others) are actively supported and any partner status.
- [ ] **South Africa.** Describe the real nature of the presence. Do not imply a physical office or name cities unless verified.
- [ ] **Atlanta office.** Add a verified street address and phone number, or remove those rows.
- [ ] **No fabricated proof.** No client logos, testimonials, certifications, awards, partner badges or statistics without evidence.

## 3. Legal

- [ ] Privacy Policy reviewed by counsel for US requirements and South Africa's POPIA (including Information Officer details and retention period).
- [ ] Terms of Service reviewed by counsel (governing law, entity details, liability).
- [ ] Registered legal entity name and address added to Privacy and Terms.
- [ ] If analytics or any cookies are added later: consent banner and Privacy Policy update first.

## 4. Content quality

- [ ] Insights articles reviewed and approved; set publication dates and `status: "published"`.
- [ ] Spelling and American English throughout.
- [ ] Every page has a unique title and description (defined in `PAGES` in `build.py`).

## 5. Accessibility (WCAG 2.2 AA)

- [ ] Keyboard-only pass: skip link, navigation menus (Enter, Escape), case study filter, contact form, all links and buttons.
- [ ] Screen reader pass (VoiceOver or NVDA) on Home, Founder and Contact: headings, landmarks, form errors announced.
- [ ] Zoom to 200% and 400% without loss of content or horizontal scrolling.
- [ ] Reduced-motion setting disables animations.
- [ ] Contrast check on any new colors or images (existing tokens pass AA).
- [ ] Alt text on real photography when added.

## 6. Security

- [ ] HTTPS everywhere with automatic certificate renewal; HSTS enabled at the proxy.
- [ ] `TRUST_PROXY=1` only when running behind your own reverse proxy.
- [ ] SMTP or CRM credentials only in server environment variables or `.env` (git-ignored), never in `public/`.
- [ ] `data/` directory backed up and readable only by the service user.
- [ ] Submit a test enquiry in production and confirm it arrives where expected.
- [ ] Check response headers (CSP, X-Frame-Options, nosniff, Referrer-Policy) on the live site.

## 7. Performance and responsiveness

- [ ] Lighthouse (mobile) on Home, Founder and Contact: Performance ≥ 90, Accessibility ≥ 95, Best Practices ≥ 95, SEO ≥ 95.
- [ ] Test on iPhone Safari, Android Chrome, iPad, laptop and large desktop.
- [ ] Optimize real photography when added (AVIF/WebP, explicit width and height, lazy-load below the fold).

## 8. SEO

- [ ] `site_url` set, then rebuild so `sitemap.xml`, canonical tags and Open Graph URLs are correct.
- [ ] Submit `sitemap.xml` to Google Search Console and Bing Webmaster Tools.
- [ ] Validate structured data with Google's Rich Results Test. Email is added automatically once verified.
- [ ] Share preview checked (LinkedIn Post Inspector) using `assets/img/og-image.png`.
