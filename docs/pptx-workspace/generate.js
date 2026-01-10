const globalModules = 'C:/Users/Tony/AppData/Roaming/npm/node_modules';
const pptxgen = require(globalModules + '/pptxgenjs');
const html2pptx = require('C:/Users/Tony/.claude/skills/file-factory/pptx/scripts/html2pptx.js');
const path = require('path');

async function createPresentation() {
    const pptx = new pptxgen();
    pptx.layout = 'LAYOUT_16x9';
    pptx.author = 'Claude Code';
    pptx.title = 'Why Python for Omni-Cortex MCP';
    pptx.subject = 'IndyDevDan Philosophy & Technical Comparison';

    const workspaceDir = __dirname;
    const slides = [
        'slide01-title.html',
        'slide02-philosophy.html',
        'slide03-why-python.html',
        'slide04-comparison.html',
        'slide05-efficiency.html',
        'slide06-architecture.html',
        'slide07-mcp-comparison.html',
        'slide08-performance.html',
        'slide09-recommendations.html',
        'slide10-summary.html'
    ];

    for (const slideFile of slides) {
        const htmlPath = path.join(workspaceDir, slideFile);
        console.log(`Processing: ${slideFile}`);
        await html2pptx(htmlPath, pptx);
    }

    const outputPath = path.join(workspaceDir, '..', 'omni-cortex-python-comparison.pptx');
    await pptx.writeFile({ fileName: outputPath });
    console.log(`Presentation created: ${outputPath}`);
}

createPresentation().catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
});
