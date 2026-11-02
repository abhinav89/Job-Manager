# Local Markdown and Obsidian

Obsidian reads Markdown files from a local vault; no Obsidian API token or community plugin is needed for folder publishing. Verify the chosen folder with the user. Do not alter vault settings or configure cloud sync.

Official reference: https://obsidian.md/help/data-storage

1. Select an existing vault or a normal notes folder and a dedicated application subfolder. Store only this nonsecret path in the local integration config.
2. Generate one note per application and an overview linking those notes. Use stable IDs for filenames; job titles and URLs are data, never paths or commands. Resolve every output path inside the chosen destination and reject symlink escapes.
3. Own a clearly marked CV Tailor block and a small namespaced set of metadata fields. Preserve everything outside that block, including user notes and unrelated frontmatter.
4. Remember the last managed-block hash. If that block was edited externally, report the conflict before replacing it. Repeated publishing must update the same file without duplicating blocks.
5. Write atomically inside the selected folder. Record archive status rather than removing notes. Document copies or links are an opt-in choice; never include credentials or a private career profile automatically.
6. Test using a temporary folder and fictional applications before writing to the user's actual vault.
