// npm install @mendable/firecrawl-js
import Firecrawl from '@mendable/firecrawl-js';

const app = new Firecrawl({ apiKey: "fc-cdb52acd54584c5386245d78307dc145"  });

// Perform a search:
app.scrape('firecrawl.dev')