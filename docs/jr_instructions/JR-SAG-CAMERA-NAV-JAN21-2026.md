# JR Instruction: Add Camera Navigation Item to SAG

**Task ID**: SAG-CAMERA-NAV
**Priority**: P1
**Created**: January 21, 2026

## Objective

Add a "Cameras" navigation item to the SAG Control Room sidebar.

## Single Task

Add one line to the SYSTEMS section in `/ganuda/home/dereadi/sag_unified_interface/templates/index.html`

Find this section (around line 44-48):
```html
<div class="nav-section">
    <h4>SYSTEMS</h4>
    <a href="#" class="nav-item" data-view="nodes">Nodes</a>
    <a href="#" class="nav-item" data-view="services">Services</a>
    <a href="#" class="nav-item" data-view="iot">IoT Devices</a>
    <a href="#" class="nav-item" data-view="homehub">Home Hub</a>
</div>
```

Add this line AFTER IoT Devices and BEFORE Home Hub:
```html
<a href="#" class="nav-item" data-view="cameras">Cameras</a>
```

Result should be:
```html
<div class="nav-section">
    <h4>SYSTEMS</h4>
    <a href="#" class="nav-item" data-view="nodes">Nodes</a>
    <a href="#" class="nav-item" data-view="services">Services</a>
    <a href="#" class="nav-item" data-view="iot">IoT Devices</a>
    <a href="#" class="nav-item" data-view="cameras">Cameras</a>
    <a href="#" class="nav-item" data-view="homehub">Home Hub</a>
</div>
```

## Output Format

**MODIFY FILE: /ganuda/home/dereadi/sag_unified_interface/templates/index.html**
Insert the camera nav item line in the appropriate location.
