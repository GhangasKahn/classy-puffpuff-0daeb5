# Standard Drawing Package Template

Use this structure for every complete fabrication package. Adapt sheet counts to project complexity but never omit a family without explicit justification.

## Title Block Requirements (every sheet)
- Project name and short code (e.g. WPF-FENCE-143-01)
- Sheet number and total (e.g. 7 / 14)
- Sheet title and code (e.g. J-101 Primary rail-to-post joint)
- Scale, units, projection method
- Revision letter and date
- Release state (CONCEPT / FABRICATION REVIEW / RELEASED FOR FABRICATION)
- Prominent banner when site verification is still required

## Recommended Sheet Families

### G — Governance
- G-001 Cover, design thesis, controlling dimensions, release basis
- G-002 Requirements matrix (ID, requirement, priority MUST/SHOULD, verification method, status)
- G-003 Given / Owner-Confirmed vs Assumed / Professional-Verify

### A — Architecture & Overall Geometry
- A-101 Dimensioned overall elevation(s)
- A-102 Plan, side views, movement envelopes, clearances
- A-103 Assembly axonometric with ballooned major assemblies (for orientation only — never scale)

### J — Joinery & Connection Details
- One sheet (or more) per unique critical joint
- Must include: geometry callouts, cut sequence, acceptance criteria, water/movement control
- Preferred format: orthographic primary views + isometric or section where clarity demands

### E — Exploded & Assembly
- E-101 Exploded assembly with insertion direction arrows
- E-102 Assembly sequence and irreversible hold points
- Solo handling notes and temporary support requirements

### F — Fabrication
- F-101 Complete part register (ID, qty, description, finished L×W×T, material, assembly)
- F-102 Stock preparation, grain orientation, rejection criteria, finish rules
- F-201 Routing / fabrication / erection sequence (numbered steps)

### S — Structural & Foundation
- S-101 Load path diagram, preliminary or final force/moment table, interaction ratios
- S-102 Foundation / pier / base connection details (or explicit hold point)
- All assumptions, safety factors, and limitations stated on the sheet

### Q — Quality, Commissioning & Maintenance
- Q-101 Inspection and acceptance plan (ID, characteristic, acceptance, method, hold/pass)
- Annual inspection items
- Seasonal configuration rules
- Maintenance intervals and procedures

## Naming Convention
ProjectCode-SheetFamily-Number  
Example: WPF-FENCE-143-01 / J-101

Keep language precise, imperative, and free of marketing fluff. Every dimension that matters for fit or strength must appear.