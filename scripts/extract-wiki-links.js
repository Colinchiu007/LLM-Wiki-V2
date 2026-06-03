#!/usr/bin/env node
// extract-wiki-links.js — Extract unique wiki-link names from all .md files in a directory
// Usage: node extract-wiki-links.js <directory> [--index <index_file>]
// Output: one link name per line, sorted unique
const fs = require('fs');
const path = require('path');

const dir = process.argv[2];
const indexFile = process.argv.includes('--index') ? process.argv[process.argv.indexOf('--index') + 1] : null;

const links = new Set();

function extractLinks(content) {
  content.replace(/\[\[([^\]]+)\]\]/g, (_, m) => {
    links.add(m.split('|')[0]);
  });
}

function walk(d) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const f = path.join(d, e.name);
    if (e.isDirectory() && e.name !== 'sessions' && e.name !== 'queries') {
      walk(f);
    } else if (e.isFile() && e.name.endsWith('.md')) {
      try {
        extractLinks(fs.readFileSync(f, 'utf8'));
      } catch (_) {}
    }
  }
}

if (indexFile) {
  try {
    extractLinks(fs.readFileSync(indexFile, 'utf8'));
  } catch (_) {}
} else {
  walk(dir);
}

for (const l of [...links].sort()) {
  console.log(l);
}
