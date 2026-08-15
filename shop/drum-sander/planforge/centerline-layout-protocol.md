# Centerline Layout Protocol for Building Construction

## Why Centerline Layout
Centerline layout is the traditional method in Japanese carpentry and high-end timber framing. It provides superior control of symmetry, joint alignment, and cumulative error compared with pure face/edge referencing, especially on posts, beams, and multi-bay structures.

## Mandatory Declaration
Every Planforge package that uses centerline layout must state clearly on the G-series and A-series sheets:

> Primary layout system: CENTERLINE  
> All critical horizontal locations originate from defined centerlines.  
> All vertical locations originate from Datum A (finished grade or other stated reference).

Never mix face/edge and centerline systems without explicit conversion notes.

## Establishing Centerlines
1. Define the primary project centerline or baseline (often the left outside face converted to center, or a true centerline of the run).
2. Establish post centerlines first. These become the governing datums for all rails, braces, and secondary members.
3. Transfer centerlines to stock using:
   - Story poles marked with center locations
   - Precision marking gauges or combination squares referenced to faces after thickness is final
   - Ink line (sumitsubo logic) for long members when appropriate
4. Verify diagonals and overall length from centerline to centerline before cutting joinery.

## Dimensioning Rules
- State post-to-post dimensions as center-to-center whenever possible.
- Rail lengths are derived from centerline spacing minus the required tenon or housing engagement on each end.
- Joint geometry (tenon length, housing depth, peg location) is always measured from the centerline or from the established reference face that was derived from the centerline.
- On drawings, use clear centerline symbols and call out “CL” consistently.

## Verification Steps (include in Q-series when centerline is used)
- Post center spacing within ±1/8" of design.
- Diagonal measurements between opposite post centers equal within 1/8".
- Rail shoulders contact fully when the frame is assembled to the design centerline spacing.
- Gate or opening clear dimensions measured from the finished faces that result from the centerline layout.

## Common Pitfalls to Guard Against
- Measuring from face on one member and centerline on another without conversion.
- Failing to account for the difference between nominal and actual post thickness when converting center-to-center to clear openings.
- Cutting tenons before confirming that the actual post centers match the story pole.

## Integration with Solo Fabrication
- Story poles and centerline gauges are preferred over repeated tape measurements for consistency.
- Temporary centerline marks on posts and rails should be preserved until final assembly and inspection are complete.