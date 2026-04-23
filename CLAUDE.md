## Website context

### Vault sync triggers
When updating the website always read from vault:

Publications list → sync from 02-articles/published/
  - Sort by year descending
  - Group by type: journal | conference | workshop
  - Format each entry from the note frontmatter

Team page → sync from 03-people/phd-students/ 
  and 03-people/postdocs/
  - Only include status: active notes

Research page → sync from 01-research/MOC-*.md
  - Use ## Core papers for selected publications per theme

Teaching page → sync from 05-admin/teaching/
  - List active courses with semester

### Update workflow
Trigger: "Sync website"
1. Read all relevant vault notes listed above
2. Generate updated content for each page
3. Show me the diff before writing any files
4. Never push to git automatically — always ask fi

@AGENTS.md
