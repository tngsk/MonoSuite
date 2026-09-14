const { mathjax } = require('mathjax-full/js/mathjax.js');
const { TeX } = require('mathjax-full/js/input/tex.js');
const { SVG } = require('mathjax-full/js/output/svg.js');
const { liteAdaptor } = require('mathjax-full/js/adaptors/liteAdaptor.js');
const { RegisterHTMLHandler } = require('mathjax-full/js/handlers/html.js');

const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);

const tex = new TeX({ packages: ['base', 'ams', 'require', 'newcommand'] });
const svg = new SVG({ fontCache: 'none' });
const html = mathjax.document('', { InputJax: tex, OutputJax: svg });

// Input read from stdin to allow arbitrary length expressions with quotes
let expr = '';
process.stdin.on('data', chunk => {
    expr += chunk;
});

process.stdin.on('end', () => {
    const isDisplay = process.argv[2] === 'true';
    try {
        const node = html.convert(expr, { display: isDisplay });
        console.log(adaptor.innerHTML(node));
    } catch (e) {
        console.error("MathJax conversion failed:", e);
        process.exit(1);
    }
});
