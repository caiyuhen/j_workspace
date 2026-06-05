const fs = require('fs');
const path = require('path');

function walk(dir) {
  let results = [];
  const list = fs.readdirSync(dir);
  list.forEach(file => {
    const filePath = path.join(dir, file);
    if (fs.statSync(filePath).isDirectory()) {
      results = results.concat(walk(filePath));
    } else if (filePath.endsWith('.tsx')) {
      results.push(filePath);
    }
  });
  return results;
}

const files = walk('client/src/pages');

files.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  
  if (content.includes("from 'antd'") && content.includes('message')) {
    // 1. remove message from antd import
    content = content.replace(/(\bimport\s+\{.*?)\bmessage\b,?/g, (match, p1) => {
      let clean = match.replace('message', '').replace(/,\s*,/g, ',').replace(/\{\s*,/g, '{').replace(/,\s*\}/g, '}');
      return clean;
    });

    // 2. Ensure App is imported from antd
    if (!content.includes('App') || (!content.includes('import { App') && !content.includes(', App'))) {
      content = content.replace(/import\s+\{(.*?)\}\s+from\s+'antd';/, "import { $1, App } from 'antd';");
      // clean up empty commas just in case
      content = content.replace(/import\s+\{\s*,\s*/g, 'import { ').replace(/,\s*\}/g, ' }');
    }

    // 3. Insert `const { message } = App.useApp();` at the beginning of the component
    const compRegex = /(const\s+[A-Z]\w*\s*(?::\s*React\.FC)?\s*=\s*\([^)]*\)\s*=>\s*\{)/;
    if (compRegex.test(content)) {
      content = content.replace(compRegex, "$1\n  const { message } = App.useApp();");
    }

    fs.writeFileSync(file, content, 'utf8');
    console.log('Fixed', file);
  }
});
