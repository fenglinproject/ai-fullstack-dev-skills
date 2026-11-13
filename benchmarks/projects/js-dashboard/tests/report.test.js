const test = require('node:test');
const assert = require('node:assert/strict');
const {summarize} = require('../src/report');
test('summarize',()=>assert.deepEqual(summarize([4,7]), {sum:11,count:2}));
