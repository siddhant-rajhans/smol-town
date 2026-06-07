import json
import os
import unittest

import app
import town


class TraceTest(unittest.TestCase):
    def test_act_records_generation_trace(self):
        original_generate = town.GENERATE
        town.GENERATE = lambda system, user: '"A tidy test line."'
        try:
            state = town.TownState()
            town.inject(state, "The bell rings.")
            state.tick = 1

            town.act(state, town.CAST[0])

            self.assertEqual(len(state.traces), 1)
            trace = state.traces[0]
            self.assertEqual(trace["tick"], 1)
            self.assertEqual(trace["speaker"], "Mayor Doreen")
            self.assertEqual(trace["role"], "mayor")
            self.assertEqual(trace["model"], town.AGENT_MODEL)
            self.assertEqual(trace["context"], ["📢: The bell rings."])
            self.assertEqual(trace["output"], "A tidy test line.")
            self.assertTrue(trace["system"].startswith("You are Mayor Doreen"))
            self.assertTrue(trace["ts"].endswith("Z"))
        finally:
            town.GENERATE = original_generate

    def test_download_trace_writes_jsonl(self):
        state = town.TownState(traces=[{"tick": 1, "output": "café"}])

        path = app.download_trace(state)
        try:
            with open(path, encoding="utf-8") as trace_file:
                self.assertEqual(json.loads(trace_file.read()), state.traces[0])
        finally:
            os.unlink(path)

    def test_download_trace_handles_missing_state(self):
        self.assertIsNone(app.download_trace(None))


if __name__ == "__main__":
    unittest.main()
