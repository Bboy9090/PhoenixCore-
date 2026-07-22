# Phase 4A Mock Writer Engine and Null Device Simulator 
 
Status: PLANNING ONLY. No real writer. 
 
Goal: Create a mock writer simulator that proves progress, cancel, resume, failure, verification, and audit events without touching a real USB drive. 
 
Safety Locks: 
- No USB writes 
- No formatting 
- No partition edits 
- No mount or unmount changes 
- No raw disk access 
- No diskpart 
- No dd 
- No writes to the selected target drive 
 
Backend Scope: 
- Add build_mock_writer_payload 
- Add null device event simulation 
- Add progress event generation 
- Add CLI simulate write flag later 
- Return JSON only 
- Do not create open or modify the target drive 
 
Required Payload: bootforge.mock_writer.v1 safe_mode true destructive false actual_write_enabled false target_type null_device 
 
Tests: successful simulation, blocked audit, missing image, progress 0 to 100, every event destructive false, no real write APIs. 
 
Forbidden: No real writer. No diskpart. No dd. No format. No raw devices. No mount changes. 
