import { PixelatedCanvas } from '@/components/ui/pixelated-canvas';
import Link from 'next/link';
import { ArrowRight, BookOpen, Dna, GitBranch, Workflow, FileText, Terminal, Code, Database, FlaskConical, Users, Github } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="flex flex-col w-full">
      {/* Hero Section - Research-focused */}
      <section className="relative px-6 py-16 md:py-24 overflow-hidden border-b">
        <div className="max-w-6xl mx-auto relative z-10">
          <div className="flex flex-col space-y-8">
            {/* Badge - Academic context */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-muted text-muted-foreground text-sm font-medium border w-fit">
              <FlaskConical className="w-4 h-4" />
              Open-source research toolkit
            </div>
            
            {/* Heading - More natural hierarchy */}
            <div className="space-y-4 max-w-3xl">
              <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-foreground" style={{ fontFamily: 'system-ui, -apple-system, sans-serif' }}>
                Chr3D
              </h1>
              
              <p className="text-xl md:text-2xl text-foreground/80 font-medium">
                A unified Python toolkit for chromosome 3D conformation analysis
              </p>
              
              <p className="text-lg text-muted-foreground leading-relaxed max-w-2xl">
                Chr3D provides an end-to-end pipeline for analyzing Hi-C, ChIA-PET, and HiChIP sequencing data. 
                Built on established tools like cooler and pairtools, it offers a consistent Python API for 
                chromatin interaction analysis—similar to how scanpy unified single-cell RNA-seq workflows.
              </p>
            </div>
            
            {/* CTA Buttons - Simplified */}
            <div className="flex flex-col gap-4 pt-2">
              <div className="flex flex-wrap gap-3">
                <Link 
                  href="/docs/getting-started"
                  className="inline-flex items-center gap-2 px-6 py-2.5 rounded-md bg-foreground text-background font-medium hover:bg-foreground/90 transition-colors"
                >
                  Documentation
                  <BookOpen className="w-4 h-4" />
                </Link>
                
                <Link 
                  href="/docs/tutorials"
                  className="inline-flex items-center gap-2 px-6 py-2.5 rounded-md border border-border bg-background font-medium hover:bg-muted transition-colors"
                >
                  <FileText className="w-4 h-4" />
                  Tutorials
                </Link>
                
                <a 
                  href="https://github.com/yourusername/chr3d"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-6 py-2.5 rounded-md border border-border bg-background font-medium hover:bg-muted transition-colors"
                >
                  <Github className="w-4 h-4" />
                  View on GitHub
                </a>
              </div>
              
              {/* Installation command - Simpler styling */}
              <div className="flex items-center gap-2.5 px-4 py-2 rounded-md bg-muted/50 border font-mono text-sm w-fit">
                <Terminal className="w-4 h-4 text-muted-foreground" />
                <code>pip install chr3d</code>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Canvas Section - Research context */}
      <section className="px-6 py-16 md:py-20 bg-muted/30">
        <div className="max-w-[90rem] mx-auto">
          <div className="mb-10 space-y-3 max-w-3xl">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
              Visualizing chromatin interactions
            </h2>
            <p className="text-base text-muted-foreground leading-relaxed">
              Contact maps reveal the spatial organization of chromosomes. This interactive visualization 
              shows Hi-C data where brighter regions indicate more frequent physical interactions between 
              genomic loci. Hover to explore the contact matrix structure.
            </p>
          </div>
          
          <div className="flex items-center justify-center">
            <div className="w-full flex justify-between gap-4 max-w-[80vw] relative">
              <PixelatedCanvas
                src="/hic_head_shot.png"
                width={1200/2}
                height={800/2}
                cellSize={8}
                dotScale={0.9}
                shape="square"
                backgroundColor="#683c02ff"
                dropoutStrength={0.01}
                interactive
                distortionStrength={0.05}
                distortionRadius={200}
                distortionMode="repel"
                followSpeed={0.2}
                jitterStrength={4}
                jitterSpeed={1}
                sampleAverage
                className="w-full h-auto border shadow-lg"
              />
                 <PixelatedCanvas
                src="/hic_head_shot.png"
                width={1200/2}
                height={800/2}
                cellSize={8}
                dotScale={0.9}
                shape="square"
                backgroundColor="#683c02ff"
                dropoutStrength={0.01}
                interactive
                distortionStrength={0.05}
                distortionRadius={200}
                distortionMode="repel"
                followSpeed={0.2}
                jitterStrength={4}
                jitterSpeed={1}
                sampleAverage
                className="w-full h-auto border shadow-lg"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Overview Section - Research problem statement */}
      <section className="px-6 py-16 md:py-20 border-t">
        <div className="max-w-4xl mx-auto space-y-10">
          <div className="space-y-3">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
              Why Chr3D?
            </h2>
            <div className="prose prose-lg max-w-none text-muted-foreground leading-relaxed space-y-4">
              <p>
                Analyzing 3D chromatin conformation data typically requires stitching together tools across 
                different languages and environments. Researchers must navigate inconsistent APIs, manage 
                complex dependencies, and write extensive glue code to connect alignment, filtering, 
                normalization, and downstream analysis steps.
              </p>
              <p>
                Chr3D addresses this by providing a unified Python framework that handles the complete workflow—from 
                raw sequencing reads to biological insights—for Hi-C, ChIA-PET, and HiChIP experiments. While the 
                underlying algorithms come from established packages like cooler and pairtools, Chr3D integrates 
                them with custom modules into a modular, extensible pipeline that's easy to install and use.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section - Research capabilities */}
      <section className="px-6 py-16 md:py-20 border-t bg-muted/30">
        <div className="max-w-6xl mx-auto">
          <div className="mb-12 space-y-3">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
              Key capabilities
            </h2>
            <p className="text-base text-muted-foreground max-w-3xl">
              Chr3D streamlines the chromatin analysis workflow with integrated tools and a consistent interface
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6">
            {/* Feature 1 */}
            <div className="rounded-lg border bg-card p-6 hover:shadow-md transition-shadow">
              <div className="flex flex-col space-y-4">
                <div className="w-11 h-11 rounded-md bg-muted flex items-center justify-center">
                  <Dna className="w-5 h-5 text-foreground" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold">Multi-assay support</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Unified workflows for Hi-C, ChIA-PET, and HiChIP with consistent APIs across different 
                    sequencing modalities.
                  </p>
                </div>
              </div>
            </div>
            
            {/* Feature 2 */}
            <div className="rounded-lg border bg-card p-6 hover:shadow-md transition-shadow">
              <div className="flex flex-col space-y-4">
                <div className="w-11 h-11 rounded-md bg-muted flex items-center justify-center">
                  <Workflow className="w-5 h-5 text-foreground" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold">Complete pipeline</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Handle alignment, quality control, filtering, matrix generation, and downstream analysis 
                    in a single framework.
                  </p>
                </div>
              </div>
            </div>
            
            {/* Feature 3 */}
            <div className="rounded-lg border bg-card p-6 hover:shadow-md transition-shadow">
              <div className="flex flex-col space-y-4">
                <div className="w-11 h-11 rounded-md bg-muted flex items-center justify-center">
                  <Code className="w-5 h-5 text-foreground" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold">Modular Python API</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Flexible, extensible design lets you customize workflows and integrate with existing 
                    analysis pipelines.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Supported Methods Section */}
      <section className="px-6 py-16 md:py-20 border-t">
        <div className="max-w-6xl mx-auto">
          <div className="mb-12 space-y-3">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
              Supported sequencing methods
            </h2>
            <p className="text-base text-muted-foreground max-w-3xl">
              Chr3D supports the three major 3C-based techniques for studying chromatin architecture
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6">
            {/* Hi-C */}
            <div className="rounded-lg border bg-card p-7 hover:shadow-md transition-shadow">
              <div className="space-y-4">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-muted">
                  <span className="text-lg font-bold text-foreground">Hi-C</span>
                </div>
                <div className="space-y-2.5">
                  <h3 className="text-lg font-semibold">Hi-C</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Genome-wide mapping of chromatin interactions for comprehensive 3D structure analysis, 
                    compartment identification, and TAD calling.
                  </p>
                  <ul className="space-y-1.5 text-sm text-muted-foreground pt-1">
                    <li className="flex items-start gap-2">
                      <span className="text-foreground/40">•</span>
                      <span>Contact matrix generation</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-foreground/40">•</span>
                      <span>Compartment calling (A/B)</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-foreground/40">•</span>
                      <span>Chromatin loop detection</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
            
            {/* ChIA-PET */}
            <div className="rounded-lg border bg-card p-7 hover:shadow-md transition-shadow">
              <div className="space-y-4">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-muted">
                  <span className="text-base font-bold text-foreground">ChIA</span>
                </div>
                <div className="space-y-2.5">
                  <h3 className="text-lg font-semibold">ChIA-PET</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Protein-mediated chromatin interactions with targeted enrichment, combining ChIP with 
                    proximity ligation for high-resolution mapping.
                  </p>
                  <ul className="space-y-1.5 text-sm text-muted-foreground pt-1">
                    <li className="flex items-start gap-2">
                      <span className="text-foreground/40">•</span>
                      <span>Linker filtering and trimming</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-foreground/40">•</span>
                      <span>PET clustering</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-foreground/40">•</span>
                      <span>Significant interaction calling</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
            
            {/* HiChIP */}
            <div className="rounded-lg border bg-card p-7 hover:shadow-md transition-shadow">
              <div className="space-y-4">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-muted">
                  <span className="text-base font-bold text-foreground">HiChIP</span>
                </div>
                <div className="space-y-2.5">
                  <h3 className="text-lg font-semibold">HiChIP</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Efficient, cost-effective method combining Hi-C with ChIP-seq enrichment to map 
                    protein-associated chromatin interactions at scale.
                  </p>
                  <ul className="space-y-1.5 text-sm text-muted-foreground pt-1">
                    <li className="flex items-start gap-2">
                      <span className="text-foreground/40">•</span>
                      <span>Quality control and filtering</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-foreground/40">•</span>
                      <span>Matrix balancing and normalization</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-foreground/40">•</span>
                      <span>Loop identification and annotation</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Quick Start Code Example */}
      <section className="px-6 py-16 md:py-20 border-t bg-muted/30">
        <div className="max-w-4xl mx-auto">
          <div className="mb-10 space-y-3">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
              Quick example
            </h2>
            <p className="text-base text-muted-foreground">
              Run a complete Hi-C analysis with just a few lines of Python code
            </p>
          </div>
          
          <div className="rounded-lg border bg-card shadow-sm overflow-hidden">
            <div className="bg-muted/50 px-5 py-3 border-b flex items-center gap-3">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500/40" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/40" />
                <div className="w-3 h-3 rounded-full bg-green-500/40" />
              </div>
              <span className="text-xs font-mono text-muted-foreground">analyze_hic.py</span>
            </div>
            <div className="p-5 bg-card overflow-x-auto">
              <pre className="font-mono text-sm leading-relaxed">
                <code className="text-foreground">
{`from chr3d import HiCPipeline

# Initialize pipeline with your data
pipeline = HiCPipeline(
    fastq1="sample_R1.fastq.gz",
    fastq2="sample_R2.fastq.gz",
    genome="hg38"
)

# Run the complete workflow
pipeline.align()
pipeline.filter_valid_pairs()
pipeline.generate_matrix(resolution=10000)
pipeline.call_tads()

# Export results
pipeline.export_cooler("output.cool")`}
                </code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* Documentation CTA - Academic style */}
      <section className="px-6 py-16 md:py-20 border-t">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="space-y-3">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
              Getting started
            </h2>
            <p className="text-base text-muted-foreground leading-relaxed max-w-2xl">
              Chr3D is under active development. We welcome contributions, bug reports, and feature requests 
              from the community. Check out the documentation to start analyzing your chromatin sequencing data.
            </p>
          </div>
          
          <div className="flex flex-wrap gap-3 pt-2">
            <Link 
              href="/docs/getting-started"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-foreground text-background font-medium hover:bg-foreground/90 transition-colors"
            >
              Read the docs
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link 
              href="/docs/tutorials"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md border border-border bg-background font-medium hover:bg-muted transition-colors"
            >
              <FileText className="w-4 h-4" />
              View tutorials
            </Link>
            <a 
              href="https://github.com/yourusername/chr3d"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md border border-border bg-background font-medium hover:bg-muted transition-colors"
            >
              <Github className="w-4 h-4" />
              Contribute on GitHub
            </a>
          </div>

          {/* Attribution and community */}
          <div className="pt-8 border-t space-y-3">
            <p className="text-sm text-muted-foreground leading-relaxed">
              Chr3D builds on excellent work from the chromatin biology and bioinformatics communities, 
              integrating tools like <a href="https://github.com/open2c/cooler" target="_blank" rel="noopener noreferrer" className="underline hover:text-foreground">cooler</a>, <a href="https://github.com/open2c/pairtools" target="_blank" rel="noopener noreferrer" className="underline hover:text-foreground">pairtools</a>, and 
              methods adapted from various open-source repositories.
            </p>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Users className="w-4 h-4" />
              <span>Open science • Computational biology research</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

// import { PixelatedCanvas } from '@/components/ui/pixelated-canvas';
// import Link from 'next/link';
// import { ArrowRight, BookOpen, Dna, GitBranch, Workflow, Sparkles, Terminal, Cpu, Database, Clock, Shield, Users } from 'lucide-react';

// export default function HomePage() {
//   return (
//     <div className="flex flex-col w-full">
//       {/* Hero Section - Enhanced with gradient background */}
//       <section className="relative px-6 py-20 md:py-32 overflow-hidden border-b bg-gradient-to-b from-background via-background to-muted/20">
//         {/* Decorative background elements */}
//         <div className="absolute inset-0 bg-grid-white/5 [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]" />
        
//         <div className="max-w-7xl mx-auto relative z-10">
//           <div className="flex flex-col items-center text-center space-y-10">
//             {/* Badge - More prominent */}
//             <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-semibold border border-primary/20 shadow-sm">
//               <Sparkles className="w-4 h-4" />
//               Unified Python Framework for Chromatin Analysis
//             </div>
            
//             {/* Heading - Improved hierarchy */}
//             <div className="space-y-6 max-w-4xl">
//               <h1 className="text-6xl md:text-8xl font-bold tracking-tight bg-gradient-to-br from-foreground to-foreground/70 bg-clip-text text-transparent">
//                 Chr3D
//               </h1>
              
//               <p className="text-2xl md:text-3xl font-bold text-foreground/90">
//                 Chromosome 3D Conformation Toolkit
//               </p>
              
//               <p className="text-xl md:text-2xl text-muted-foreground leading-relaxed max-w-3xl mx-auto">
//                 End-to-end chromatin sequencing analysis from raw reads to biological insights. 
//                 Unified support for Hi-C, ChIA-PET, and HiChIP workflows.
//               </p>
//             </div>
            
//             {/* CTA Buttons - Enhanced with pip install snippet */}
//             <div className="flex flex-col items-center gap-6 pt-4 w-full max-w-2xl">
//               <div className="flex flex-wrap gap-4 justify-center">
//                 <Link 
//                   href="/docs/getting-started"
//                   className="group inline-flex items-center gap-2 px-8 py-4 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-all shadow-lg hover:shadow-xl hover:scale-105"
//                 >
//                   Get Started
//                   <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
//                 </Link>
                
//                 <Link 
//                   href="/docs/getting-started"
//                   className="inline-flex items-center gap-2 px-8 py-4 rounded-lg border-2 border-border bg-background/50 backdrop-blur-sm font-semibold hover:bg-accent hover:text-accent-foreground transition-all shadow-sm hover:shadow-md"
//                 >
//                   <BookOpen className="w-4 h-4" />
//                   Documentation
//                 </Link>
//               </div>
              
//               {/* Installation command */}
//               <div className="flex items-center gap-3 px-6 py-3 rounded-lg bg-muted/60 backdrop-blur-sm border font-mono text-sm text-muted-foreground shadow-sm">
//                 <Terminal className="w-4 h-4 text-primary" />
//                 <code className="text-foreground">pip install chr3d</code>
//               </div>
//             </div>

//             {/* Quick stats badges */}
//             <div className="flex flex-wrap justify-center gap-6 pt-8 text-sm">
//               <div className="flex items-center gap-2 text-muted-foreground">
//                 <Cpu className="w-4 h-4 text-primary" />
//                 <span className="font-medium">GPU Accelerated</span>
//               </div>
//               <div className="flex items-center gap-2 text-muted-foreground">
//                 <Database className="w-4 h-4 text-primary" />
//                 <span className="font-medium">Cooler Integration</span>
//               </div>
//               <div className="flex items-center gap-2 text-muted-foreground">
//                 <Shield className="w-4 h-4 text-primary" />
//                 <span className="font-medium">Production Ready</span>
//               </div>
//             </div>
//           </div>
//         </div>
//       </section>

//       {/* Interactive Canvas Section - Added context */}
//       <section className="px-6 py-20 md:py-24 bg-gradient-to-b from-muted/20 to-background">
//         <div className="max-w-[90rem] mx-auto">
//           <div className="text-center mb-12 space-y-4">
//             <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
//               Visualize Chromatin Interactions
//             </h2>
//             <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
//               Interactive Hi-C contact map visualization. Hover to explore the 3D genome structure.
//             </p>
//           </div>
          
//           <div className="flex items-center justify-center">
//             <div className="w-full max-w-[80vw] relative group">
//               <PixelatedCanvas
//                 src="/hic_head_shot.png"
//                 width={1200}
//                 height={800}
//                 cellSize={8}
//                 dotScale={0.9}
//                 shape="square"
//                 backgroundColor="#683c02ff"
//                 dropoutStrength={0.01}
//                 interactive
//                 distortionStrength={0.05}
//                 distortionRadius={200}
//                 distortionMode="repel"
//                 followSpeed={0.2}
//                 jitterStrength={4}
//                 jitterSpeed={1}
//                 sampleAverage
//                 className="w-full h-auto rounded-xl border shadow-xl group-hover:shadow-2xl transition-shadow"
//               />
//               <div className="absolute inset-0 rounded-xl ring-1 ring-inset ring-foreground/10 pointer-events-none" />
//             </div>
//           </div>
//         </div>
//       </section>

//       {/* Features Section - Enhanced with better visual hierarchy */}
//       <section className="px-6 py-20 md:py-24 border-t bg-muted/30">
//         <div className="max-w-7xl mx-auto">
//           <div className="text-center mb-16 space-y-4">
//             <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold border border-primary/20 mb-4">
//               FEATURES
//             </div>
//             <h2 className="text-4xl md:text-5xl font-bold tracking-tight">
//               End-to-End Chromatin Analysis
//             </h2>
//             <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
//               Everything you need for 3D chromosome conformation analysis in one unified, production-ready toolkit
//             </p>
//           </div>
          
//           <div className="grid md:grid-cols-3 gap-8">
//             {/* Feature 1 - Enhanced */}
//             <div className="group rounded-xl border bg-card p-8 shadow-sm hover:shadow-xl transition-all hover:-translate-y-1">
//               <div className="flex flex-col space-y-5">
//                 <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center group-hover:scale-110 transition-transform">
//                   <Dna className="w-7 h-7 text-primary" />
//                 </div>
//                 <div className="space-y-3">
//                   <h3 className="text-2xl font-bold">Multi-Method Support</h3>
//                   <p className="text-muted-foreground leading-relaxed">
//                     Comprehensive support for Hi-C, ChIA-PET, and HiChIP sequencing techniques with unified workflows and consistent APIs.
//                   </p>
//                 </div>
//               </div>
//             </div>
            
//             {/* Feature 2 - Enhanced */}
//             <div className="group rounded-xl border bg-card p-8 shadow-sm hover:shadow-xl transition-all hover:-translate-y-1">
//               <div className="flex flex-col space-y-5">
//                 <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center group-hover:scale-110 transition-transform">
//                   <Workflow className="w-7 h-7 text-primary" />
//                 </div>
//                 <div className="space-y-3">
//                   <h3 className="text-2xl font-bold">Streamlined Pipeline</h3>
//                   <p className="text-muted-foreground leading-relaxed">
//                     From alignment to downstream analysis, handle complete workflows with integrated tools like cooler, pairtools, and custom modules.
//                   </p>
//                 </div>
//               </div>
//             </div>
            
//             {/* Feature 3 - Enhanced */}
//             <div className="group rounded-xl border bg-card p-8 shadow-sm hover:shadow-xl transition-all hover:-translate-y-1">
//               <div className="flex flex-col space-y-5">
//                 <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center group-hover:scale-110 transition-transform">
//                   <GitBranch className="w-7 h-7 text-primary" />
//                 </div>
//                 <div className="space-y-3">
//                   <h3 className="text-2xl font-bold">Flexible Python API</h3>
//                   <p className="text-muted-foreground leading-relaxed">
//                     Modular, extensible design lets you customize workflows and integrate seamlessly with your existing analysis pipelines.
//                   </p>
//                 </div>
//               </div>
//             </div>
//           </div>
//         </div>
//       </section>

//       {/* Supported Methods Section - Enhanced with better visual distinction */}
//       <section className="px-6 py-20 md:py-24 border-t bg-gradient-to-b from-background to-muted/20">
//         <div className="max-w-7xl mx-auto">
//           <div className="text-center mb-16 space-y-4">
//             <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold border border-primary/20 mb-4">
//               METHODS
//             </div>
//             <h2 className="text-4xl md:text-5xl font-bold tracking-tight">
//               Supported Sequencing Methods
//             </h2>
//             <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
//               Analyze chromatin interactions with industry-standard 3C-derived techniques
//             </p>
//           </div>
          
//           <div className="grid md:grid-cols-3 gap-8">
//             {/* Hi-C - Enhanced */}
//             <div className="group rounded-xl border bg-card p-10 shadow-sm hover:shadow-xl transition-all hover:-translate-y-1 hover:border-primary/50">
//               <div className="space-y-5">
//                 <div className="inline-flex items-center justify-center w-16 h-16 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 group-hover:scale-110 transition-transform">
//                   <span className="text-2xl font-bold text-primary">Hi-C</span>
//                 </div>
//                 <div className="space-y-3">
//                   <h3 className="text-2xl font-bold">Hi-C Analysis</h3>
//                   <p className="text-muted-foreground leading-relaxed">
//                     Genome-wide chromatin interaction mapping for comprehensive 3D structure analysis and TAD identification
//                   </p>
//                   <ul className="space-y-2 text-sm text-muted-foreground pt-2">
//                     <li className="flex items-center gap-2">
//                       <div className="w-1 h-1 rounded-full bg-primary" />
//                       Contact matrix generation
//                     </li>
//                     <li className="flex items-center gap-2">
//                       <div className="w-1 h-1 rounded-full bg-primary" />
//                       Compartment calling
//                     </li>
//                     <li className="flex items-center gap-2">
//                       <div className="w-1 h-1 rounded-full bg-primary" />
//                       Loop detection
//                     </li>
//                   </ul>
//                 </div>
//               </div>
//             </div>
            
//             {/* ChIA-PET - Enhanced */}
//             <div className="group rounded-xl border bg-card p-10 shadow-sm hover:shadow-xl transition-all hover:-translate-y-1 hover:border-primary/50">
//               <div className="space-y-5">
//                 <div className="inline-flex items-center justify-center w-16 h-16 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 group-hover:scale-110 transition-transform">
//                   <span className="text-xl font-bold text-primary">ChIA</span>
//                 </div>
//                 <div className="space-y-3">
//                   <h3 className="text-2xl font-bold">ChIA-PET Analysis</h3>
//                   <p className="text-muted-foreground leading-relaxed">
//                     Protein-mediated chromatin interaction analysis with targeted enrichment and peak calling
//                   </p>
//                   <ul className="space-y-2 text-sm text-muted-foreground pt-2">
//                     <li className="flex items-center gap-2">
//                       <div className="w-1 h-1 rounded-full bg-primary" />
//                       Linker filtering
//                     </li>
//                     <li className="flex items-center gap-2">
//                       <div className="w-1 h-1 rounded-full bg-primary" />
//                       PET clustering
//                     </li>
//                     <li className="flex items-center gap-2">
//                       <div className="w-1 h-1 rounded-full bg-primary" />
//                       Interaction calling
//                     </li>
//                   </ul>
//                 </div>
//               </div>
//             </div>
            
//             {/* HiChIP - Enhanced */}
//             <div className="group rounded-xl border bg-card p-10 shadow-sm hover:shadow-xl transition-all hover:-translate-y-1 hover:border-primary/50">
//               <div className="space-y-5">
//                 <div className="inline-flex items-center justify-center w-16 h-16 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 group-hover:scale-110 transition-transform">
//                   <span className="text-xl font-bold text-primary">HiChIP</span>
//                 </div>
//                 <div className="space-y-3">
//                   <h3 className="text-2xl font-bold">HiChIP Analysis</h3>
//                   <p className="text-muted-foreground leading-relaxed">
//                     Combined ChIP and chromosome conformation capture for efficient, cost-effective analysis
//                   </p>
//                   <ul className="space-y-2 text-sm text-muted-foreground pt-2">
//                     <li className="flex items-center gap-2">
//                       <div className="w-1 h-1 rounded-full bg-primary" />
//                       Quality control
//                     </li>
//                     <li className="flex items-center gap-2">
//                       <div className="w-1 h-1 rounded-full bg-primary" />
//                       Normalization
//                     </li>
//                     <li className="flex items-center gap-2">
//                       <div className="w-1 h-1 rounded-full bg-primary" />
//                       Loop identification
//                     </li>
//                   </ul>
//                 </div>
//               </div>
//             </div>
//           </div>
//         </div>
//       </section>

//       {/* Quick Start Code Example - NEW SECTION */}
//       <section className="px-6 py-20 md:py-24 border-t bg-muted/30">
//         <div className="max-w-5xl mx-auto">
//           <div className="text-center mb-12 space-y-4">
//             <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold border border-primary/20 mb-4">
//               QUICK START
//             </div>
//             <h2 className="text-4xl md:text-5xl font-bold tracking-tight">
//               Get Running in Minutes
//             </h2>
//             <p className="text-xl text-muted-foreground">
//               Simple, intuitive API for chromatin analysis
//             </p>
//           </div>
          
//           <div className="rounded-xl border bg-card shadow-xl overflow-hidden">
//             <div className="bg-muted/50 px-6 py-4 border-b flex items-center justify-between">
//               <div className="flex items-center gap-3">
//                 <div className="flex gap-2">
//                   <div className="w-3 h-3 rounded-full bg-red-500/60" />
//                   <div className="w-3 h-3 rounded-full bg-yellow-500/60" />
//                   <div className="w-3 h-3 rounded-full bg-green-500/60" />
//                 </div>
//                 <span className="text-sm font-mono text-muted-foreground">analyze_hic.py</span>
//               </div>
//             </div>
//             <div className="p-6 bg-card">
//               <pre className="font-mono text-sm leading-relaxed overflow-x-auto">
//                 <code className="text-foreground">
// {`from chr3d import HiCPipeline

// # Initialize pipeline
// pipeline = HiCPipeline(
//     fastq1="sample_R1.fastq.gz",
//     fastq2="sample_R2.fastq.gz",
//     genome="hg38"
// )

// # Run end-to-end analysis
// pipeline.align()
// pipeline.filter_valid_pairs()
// pipeline.generate_matrix(resolution=10000)
// pipeline.call_tads()

// # Export results
// pipeline.export_cooler("output.cool")`}
//                 </code>
//               </pre>
//             </div>
//           </div>
//         </div>
//       </section>

//       {/* CTA Section - Enhanced */}
//       <section className="px-6 py-24 md:py-32 border-t bg-gradient-to-b from-muted/20 to-background">
//         <div className="max-w-4xl mx-auto text-center space-y-8">
//           <div className="space-y-4">
//             <h2 className="text-4xl md:text-5xl font-bold tracking-tight">
//               Ready to explore chromosome 3D conformations?
//             </h2>
//             <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
//               Join researchers using Chr3D to accelerate chromatin sequencing analysis and unlock insights into genome organization
//             </p>
//           </div>
          
//           <div className="flex flex-col sm:flex-row justify-center gap-4 pt-4">
//             <Link 
//               href="/docs/getting-started"
//               className="group inline-flex items-center gap-2 px-8 py-4 rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-all shadow-lg hover:shadow-xl hover:scale-105"
//             >
//               View Documentation
//               <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
//             </Link>
//             <Link 
//               href="/docs/tutorials"
//               className="inline-flex items-center gap-2 px-8 py-4 rounded-lg border-2 border-border bg-background/50 backdrop-blur-sm font-semibold hover:bg-accent hover:text-accent-foreground transition-all shadow-sm hover:shadow-md"
//             >
//               <BookOpen className="w-4 h-4" />
//               Explore Tutorials
//             </Link>
//           </div>

//           {/* Social proof / Community */}
//           <div className="flex items-center justify-center gap-2 pt-8 text-sm text-muted-foreground">
//             <Users className="w-4 h-4" />
//             <span>Trusted by computational biology researchers worldwide</span>
//           </div>
//         </div>
//       </section>
//     </div>
//   );
// }
