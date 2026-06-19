import sys, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.append(str(Path(__file__).parent.parent))
import usb_creator

def audit(ok=True,size=3145728):
    return {"schema":"bootforge.write_plan_audit.v1","validation_status":"passed" if ok else "failed","safe_mode":True,"destructive":False,"operation":"dry_run_write_plan_audit","plan_id":"bootforge-plan-test","plan_hash":"hash","eligible":ok,"blocked":not ok,"block_reasons":[] if ok else ["System drive blocked."],"checks":[],"write_plan":{"target_drive":"E:\\","image_path":"test.img","image_inspection":{"image":{"path":"test.img","filename":"test.img","exists":True,"supported":True,"size_bytes":size,"sha256":"abc"}}},"error":None}

class TestMockWriter(unittest.TestCase):
    @patch("usb_creator.build_write_plan_audit_payload")
    def test_success_progress_and_shape(self,m):
        m.return_value=audit(True,3*1024*1024)
        p=usb_creator.build_mock_writer_payload("E:\\","test.img",chunk_size=1024*1024)
        self.assertEqual("bootforge.mock_writer.v1",p["schema"])
        self.assertEqual("null_device",p["target_type"])
        self.assertEqual("completed",p["status"])
        self.assertFalse(p["destructive"])
        self.assertFalse(p["actual_write_enabled"])
        self.assertEqual(3,p["chunks_completed"])
        self.assertEqual(0,p["events"][0]["progress"])
        self.assertEqual(100,p["events"][-1]["progress"])
    @patch("usb_creator.build_write_plan_audit_payload")
    def test_blocked_when_audit_fails(self,m):
        m.return_value=audit(False)
        p=usb_creator.build_mock_writer_payload("C:\\","test.img")
        self.assertEqual("blocked",p["status"])
        self.assertTrue(p["blocked"])
        self.assertEqual("simulation_blocked",p["events"][0]["type"])
    @patch("usb_creator.build_write_plan_audit_payload")
    def test_missing_image_size_blocks(self,m):
        m.return_value=audit(True,0)
        p=usb_creator.build_mock_writer_payload("E:\\","missing.img")
        self.assertEqual("blocked",p["status"])
        self.assertIn("Image size is zero",p["block_reasons"][0])
    @patch("usb_creator.build_write_plan_audit_payload")
    def test_failure_and_cancel_injection(self,m):
        m.return_value=audit(True,3*1024*1024)
        f=usb_creator.build_mock_writer_payload("E:\\","test.img",chunk_size=1024*1024,fail_at_chunk=2)
        c=usb_creator.build_mock_writer_payload("E:\\","test.img",chunk_size=1024*1024,cancel_at_chunk=2)
        self.assertEqual("failed",f["status"])
        self.assertEqual("cancelled",c["status"])
    @patch("usb_creator.build_write_plan_audit_payload")
    def test_every_event_non_destructive(self,m):
        m.return_value=audit(True,2*1024*1024)
        p=usb_creator.build_mock_writer_payload("E:\\","test.img",chunk_size=1024*1024)
        self.assertTrue(p["events"])
        for e in p["events"]:
            self.assertIs(e.get("destructive"),False)

if __name__=="__main__":
    unittest.main()
