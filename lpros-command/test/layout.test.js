import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { applyDeskLayout, snapLayout, snapName } from "../public/layout.js";

describe("desk layout snap", () => {
  it("names layouts across phone → ultra without gaps", () => {
    assert.equal(snapName(320), "phone");
    assert.equal(snapName(559), "phone");
    assert.equal(snapName(560), "phablet");
    assert.equal(snapName(799), "phablet");
    assert.equal(snapName(800), "tablet");
    assert.equal(snapName(1099), "tablet");
    assert.equal(snapName(1100), "laptop");
    assert.equal(snapName(1439), "laptop");
    assert.equal(snapName(1440), "desk");
    assert.equal(snapName(1919), "desk");
    assert.equal(snapName(1920), "wide");
    assert.equal(snapName(2559), "wide");
    assert.equal(snapName(2560), "ultra");
    assert.equal(snapName(5120), "ultra");
  });

  it("phones stack the VM unless landscape is short", () => {
    const portrait = snapLayout(390, 844);
    assert.equal(portrait.name, "phone");
    assert.equal(portrait.rail, "top");
    assert.equal(portrait.vm, "bottom");
    assert.equal(portrait.landscape, false);

    const land = snapLayout(780, 360);
    assert.equal(land.name, "phablet");
    assert.equal(land.rail, "top");
    assert.equal(land.vm, "side");
    assert.equal(land.short, true);
  });

  it("tablets compact the rail in landscape and stack VM in portrait", () => {
    const land = snapLayout(1024, 768);
    assert.equal(land.name, "tablet");
    assert.equal(land.rail, "compact");
    assert.equal(land.vm, "side");

    const port = snapLayout(900, 1200);
    assert.equal(port.name, "tablet");
    assert.equal(port.rail, "top");
    assert.equal(port.vm, "bottom");
  });

  it("desk and ultra keep a side rail + side VM with fluid vars", () => {
    const desk = snapLayout(1600, 900);
    assert.equal(desk.name, "desk");
    assert.equal(desk.rail, "side");
    assert.equal(desk.vm, "side");
    assert.match(desk.vars["--rail-w"], /px$/);
    assert.ok(Number(desk.vars["--vm-fr"]) > 0);

    const ultra = snapLayout(3840, 2160);
    assert.equal(ultra.name, "ultra");
    assert.equal(ultra.rail, "side");
    assert.equal(ultra.vm, "side");
  });

  it("applyDeskLayout writes data attributes and CSS vars", () => {
    const el = { dataset: {}, style: { props: {}, setProperty(k, v) { this.props[k] = v; } } };
    applyDeskLayout(el, snapLayout(1440, 900));
    assert.equal(el.dataset.layout, "desk");
    assert.equal(el.dataset.rail, "side");
    assert.equal(el.dataset.vm, "side");
    assert.equal(el.dataset.orient, "landscape");
    assert.ok(el.style.props["--desk-w"]);
  });
});
