# AI Prompt Repository Research v6

## Current catalog
- 93 repositories tracked
- 73 active repositories
- 63 prompt corpora
- 10 active tooling repositories
- 15 verified originals
- 58 probable originals
- 19 candidates awaiting further verification
- 1 explicit duplicate exclusion
- 36 model families

## Verification policy
`verified_original` means GitHub metadata was directly checked and `fork=false` was confirmed. `probable_original` means no strong duplicate/fork signal was found in the current audit but it has not received the same direct verification.

Origin verification, content quality, and license verification are separate dimensions. A repository can be original but still have an unverified license or weak/incorrect marketing metadata.

## Important audited additions
- Qwen Image 3 corpus: repository metadata says `fork=false`; its README was inspected and records 144 original prompt recipes across 18 categories plus reusable templates. The repository description's larger count is therefore not used as the verified corpus count.
- LTX Video prompt cookbook: repository metadata says `fork=false`; a real `prompts/` directory was verified with camera movements, character dialogue, cinematic scenes, image-to-video, product video, and synchronized audio materials.
- Higgsfield Prompt Skill: repository metadata says `fork=false`; treated as tooling, not core corpus, because it is a prompt skill/framework covering cinematic video workflows rather than simply a prompt dataset.

## Default collection policy
- Download only active `corpus` and optional `tooling`.
- Exclude `candidate` and `duplicate_excluded` by default.
- Use text-only sparse checkout and skip Git LFS smudge to avoid downloading large visual assets that are not needed for prompt indexing.
- Exact prompt duplicates are automatically consolidated.
- Near duplicates are review-only and are never automatically deleted.
