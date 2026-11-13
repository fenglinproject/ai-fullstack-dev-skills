#!/usr/bin/env node
'use strict';
// AST-only reader. Never imports, evaluates or executes project code or tsconfig.
const fs = require('node:fs');
const path = require('node:path');
function compiler() {
  try { return require('typescript'); } catch (_) {}
  // Node's global TypeScript installation; not the inspected project's node_modules.
  try { return require(path.resolve(path.dirname(process.execPath), '../lib/node_modules/typescript')); } catch (_) {}
  throw new Error('TypeScript compiler unavailable: install typescript in the tool environment (npm install -g typescript@5.9.3)');
}
const ts = compiler();
function run(items) {
  if (!Array.isArray(items) || items.length > 128) throw new Error('invalid parse batch');
  const out = [];
  for (const item of items) {
    if (!item || typeof item.path !== 'string' || typeof item.source !== 'string' || item.source.length > 300000) throw new Error('invalid source');
    const rel = item.path;
    const kind = /\.(tsx|jsx)$/.test(rel) ? ts.ScriptKind.TSX : /\.(ts|mts|cts)$/.test(rel) ? ts.ScriptKind.TS : ts.ScriptKind.JS;
    const sf = ts.createSourceFile(rel, item.source, ts.ScriptTarget.Latest, true, kind);
    const symbols = [], references = [], imports = [];
    let dynamic = false;
    const line = n => sf.getLineAndCharacterOfPosition(n.getStart(sf)).line + 1;
    const endLine = n => sf.getLineAndCharacterOfPosition(n.end).line + 1;
    function visit(node, scope) {
      let name = null, kindName = null;
      if (ts.isClassDeclaration(node) || ts.isClassExpression(node)) {kindName='class';name=node.name?.text;}
      else if (ts.isFunctionDeclaration(node)) {kindName='function';name=node.name?.text;}
      else if (ts.isMethodDeclaration(node) || ts.isMethodSignature(node)) {kindName='method';name=node.name && (ts.isIdentifier(node.name) || ts.isStringLiteral(node.name)) ? node.name.text : null;}
      else if (ts.isInterfaceDeclaration(node)) {kindName='interface';name=node.name.text;}
      else if (ts.isTypeAliasDeclaration(node)) {kindName='type';name=node.name.text;}
      else if (ts.isEnumDeclaration(node)) {kindName='enum';name=node.name.text;}
      else if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name)) {
        kindName = node.initializer && (ts.isArrowFunction(node.initializer) || ts.isFunctionExpression(node.initializer)) ? 'function_variable' : 'variable';
        name=node.name.text;
      }
      const nextScope = name && kindName !== 'variable' ? [...scope,name] : scope;
      if (name && symbols.length < 3000) symbols.push({path:rel,name,qualified_name:[...scope,name].join('.'),kind:kindName,line:line(node),end_line:endLine(node)});
      if ((ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) && node.moduleSpecifier && ts.isStringLiteral(node.moduleSpecifier)) {
        imports.push(node.moduleSpecifier.text);
      }
      if (ts.isCallExpression(node)) {
        const expression=node.expression;
        if (expression.kind === ts.SyntaxKind.ImportKeyword) {
          if (node.arguments.length===1 && ts.isStringLiteral(node.arguments[0])) imports.push(node.arguments[0].text);
          else dynamic=true;
        } else if (ts.isIdentifier(expression) && expression.text==='require') {
          if (node.arguments.length===1 && ts.isStringLiteral(node.arguments[0])) imports.push(node.arguments[0].text);
          else dynamic=true;
        }
        let called=null;
        if (ts.isIdentifier(expression)) called=expression.text;
        else if (ts.isPropertyAccessExpression(expression)) called=expression.name.text;
        if (called && references.length < 5000) references.push({path:rel,name:called,line:line(node),scope:scope.join('.')});
      }
      ts.forEachChild(node, child=>visit(child,nextScope));
    }
    visit(sf,[]);
    out.push({path:rel,symbols,references,imports:[...new Set(imports)].sort(),dynamic_imports:dynamic,
      parse_errors:sf.parseDiagnostics.slice(0,5).map(d=>({line:sf.getLineAndCharacterOfPosition(d.start || 0).line+1,code:d.code}))});
  }
  return out;
}
let input='';
process.stdin.setEncoding('utf8');
process.stdin.on('data',chunk=>{input+=chunk; if (input.length>12000000) {console.error('batch too large');process.exit(2);}});
process.stdin.on('end',()=>{
  try { const payload=JSON.parse(input);process.stdout.write(JSON.stringify({files:run(payload.items)})); }
  catch(e) {console.error(String(e.message).slice(0,300));process.exitCode=2;}
});
