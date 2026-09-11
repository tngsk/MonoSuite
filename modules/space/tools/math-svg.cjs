// Build-time only. Base + AMS; no HTML, URL, dynamic loading, or macro-definition packages.
const {mathjax} = require('mathjax-full/js/mathjax.js');
const {TeX} = require('mathjax-full/js/input/tex.js');
const {SVG} = require('mathjax-full/js/output/svg.js');
const {liteAdaptor} = require('mathjax-full/js/adaptors/liteAdaptor.js');
const {RegisterHTMLHandler} = require('mathjax-full/js/handlers/html.js');
require('mathjax-full/js/input/tex/ams/AmsConfiguration.js');
const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const {tex, display} = JSON.parse(input);
    const document = mathjax.document('', {
      InputJax: new TeX({packages: ['base', 'ams'], maxBuffer: 10000,
        formatError: (_jax, error) => { throw Error(error.message); }}),
      OutputJax: new SVG({fontCache: 'none'})
    });
    const node = document.convert(tex, {display, em: 16, ex: 8, containerWidth: 768});
    const svg = adaptor.firstChild(node);
    const markup = adaptor.outerHTML(svg);
    if (markup.includes('data-mml-node="merror"')) throw Error('数式を解釈できません');
    process.stdout.write(JSON.stringify({svg: markup}));
  } catch (error) {
    process.stderr.write(error.message);
    process.exitCode = 1;
  }
});
