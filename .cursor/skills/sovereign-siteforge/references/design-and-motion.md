# SOVEREIGN SITEFORGE — Design & Motion Genome

## Governing Creative Concept

Before designing, produce an internal concept statement:

- Strategic thesis
- Central visual metaphor
- Narrative spine
- Emotional movement
- Signature interaction
- Signature material or texture
- Typographic role
- Motion behavior
- Primary conversion moment
- What the design deliberately refuses to resemble

Select the strongest coherent direction and build it. Do not present multiple concepts unless the user asks.

## Emotional Arc (Five Acts)

Treat the site as a composed sequence.

**Act I — Arrival**  
Establish atmosphere, signal category and difference, clarify enough to prevent confusion, create immediate reason to continue.

**Act II — Recognition**  
Show understanding of the visitor, name the problem with specificity, introduce tension.

**Act III — Revelation**  
Reveal the mechanism, demonstrate how the offering works, create the primary “I understand it now” moment.

**Act IV — Proof**  
Resolve skepticism, show evidence, answer objections, make comparison easier.

**Act V — Resolution**  
Present transformation, reduce remaining risk, invite the next action, leave a memorable final image or idea.

Visual density, pacing, motion, and copy rhythm must change between acts. Do not make every section equally loud.

## Information Architecture

Choose page count and section architecture based on the offer (short-cycle vs high-consideration, product/software, service, local, portfolio, craft/heritage, scientific/medical/financial, nonprofit).

Prioritize according to category needs. Do not force a universal section order.

## Component Morphology

No component has a universally fixed appearance. Navigation, opening composition, feature/value communication, pricing, status indicators, and footer must be derived from the concept.

Opening composition options include typographic monument, cinematic scene, product demonstration, split narrative, interactive question, material close-up, editorial cover, spatial diagram, live calculation, founder declaration, documentary fragment, interactive object, quiet statement with delayed reveal.

Do not default to centered copy over a gradient or stock photograph.

Feature structures may include interactive product artifact, annotated mechanism, comparison lens, before/after, scrolling evidence sequence, exploded diagram, material specimen, case-study fragments, editorial chapters, dynamic calculator, decision tree, timeline, process table, use-case constellation. Choose the form that best proves the value.

## Typography System

Assign roles: Display voice, Reading voice, Utility voice, Data/technical voice (only if required), Accent voice (only if meaningful).

For each: typeface, weight range, optical size, tracking, line height, case behavior, max line length, responsive scale, fallback stack.

Avoid serif italic solely for luxury, monospace solely for tech, compressed grotesk solely for brutalism, five+ typefaces, unreadably thin weights, excessive all-caps, giant text that breaks mobile.

## Color, Surface, Material

Generate semantic tokens for background, elevated/recessed surface, primary/secondary text, accent, action, focus, success/warning/error, border, selection.

Derive from brand character, category conventions, emotional objective, material references, imagery, contrast requirements.

Do not force cream backgrounds, neon accents, dark mode, noise, gradients, large radii, or sharp corners. Select edge radius, border, depth, grain, and texture from the governing concept.

## Motion Direction

Define perceived mass, tempo, acceleration/deceleration, travel distance, rhythm, staggering, response latency, transition duration, spatial direction, motion hierarchy.

Select one coherent motion personality (heavy/architectural, precise/mechanical, soft/biological, abrupt/editorial, restrained/luxurious, elastic/playful, ritualistic/slow, immediate/utilitarian).

Every animation must serve at least one purpose: orient, reveal hierarchy, show causality, demonstrate function, explain transformation, provide feedback, maintain spatial continuity, reward completion, intensify a deliberate emotional beat.

Delete motion that exists only because animation is possible.

Respect `prefers-reduced-motion`. Provide nonessential-motion control when substantial animation exists. Reduced-motion mode must preserve all information and controls.

When using professional animation libraries: scope to component/route, clean up contexts/observers/triggers, prevent duplicate animation, prefer transform/opacity, verify resize/orientation, ensure fallback visibility, maintain focus and reading order.

## Signature Interaction

Create one interaction uniquely tied to the brand’s mechanism or metaphor.

It must be understandable, have a non-animated equivalent, work on touch and pointer, work without precision dragging, avoid blocking primary conversion, provide immediate feedback, reveal meaningful information, remain performant, and be fully implemented.

## Performance Budget

Target good Core Web Vitals: LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1.

Require correctly sized responsive images, modern formats, explicit dimensions or stable aspect ratios, lazy loading below fold, minimal font families, removal of unused dependencies, no giant uncompressed video, animation pausing outside viewport, stable layout during load, graceful behavior on slower mobile.

## Accessibility Requirements

Target WCAG 2.2 Level AA (stronger practices when practical).

Require semantic landmarks, logical heading hierarchy, skip link, full keyboard operation, no keyboard traps, visible focus, accessible names, labels/instructions, descriptive links, text alternatives, sufficient contrast, text resizing, responsive reflow, logical reading order, reduced-motion support, pause/stop for moving content, accessible form errors, status announcements, adequate touch targets, single-pointer alternatives, no color-only communication, no rapid flashing.

Treat accessibility failures as design failures.
