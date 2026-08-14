#!/usr/bin/env python3
from __future__ import annotations
import subprocess, sys, unittest
from pathlib import Path
class PdfLoopxHarnessIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls)->None: cls.root=Path(__file__).resolve().parents[1]
    def run_gate(self,*extra:str)->subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable,"scripts/gates/check_pdf_loopx_harness_integration.py",*extra],cwd=self.root,check=False,capture_output=True,text=True)
    def test_current_contract(self)->None:
        completed=self.run_gate(); self.assertEqual(completed.returncode,0,completed.stdout+completed.stderr)
    def test_mutation_controls(self)->None:
        completed=self.run_gate("--selftest"); self.assertEqual(completed.returncode,0,completed.stdout+completed.stderr); self.assertIn("13 mutations",completed.stdout)
if __name__=="__main__": unittest.main()
