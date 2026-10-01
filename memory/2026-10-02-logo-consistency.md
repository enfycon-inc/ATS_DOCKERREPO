# Header logo consistency

- Symptom: default branding flashes, then tenant logo appears small or grows.
- Root cause: unresolved branding was treated as no custom logo; the renderer
  painted the full padded image before replacing it with a cropped SVG. Auto
  width changed the footprint between these two states.
- Fix: brandingReady distinguishes undefined logo from explicit null/empty.
  Header reserves a 240 x 34 slot (28 x 28 collapsed), preserving proportions.
  Unmeasured artwork is hidden until its final bounds are ready. Partial profile
  replies preserve previously known branding. Failed initial requests leave a
  neutral empty slot rather than displaying an unconfirmed platform logo.
- Files: contexts/tenant-branding.tsx, components/layout/navbar-logo.tsx,
  components/shared/company-logo-image.tsx.
- Evidence: three new regressions failed before changes; nine focused branding
  and logo cases pass afterward, including real component execution with mocked
  hooks/canvas. Full suite: 48 passed, 11 existing unrelated failures.
  Diff check passed. TypeScript fails on unrelated job-posting/new/page.tsx:30
  calling nonexistent auth.getMe. That file was not changed by this fix.
- Regression tests: tests/company-logo-image.test.cjs and tenant-branding.test.cjs.
- Related: prior September 23 branding report, October 1 login recording.
  The recording shows a small logo but does not itself establish a size transition.
- Status: DONE_WITH_CONCERNS. No signed-in browser was connected, so live visual
  verification remains outstanding. Uploaded files/database were not changed.
