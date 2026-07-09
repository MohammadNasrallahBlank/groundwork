JUNIT = """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
<testsuite name="pytest" errors="0" failures="1" skipped="0" tests="2" time="0.041">
<testcase classname="tests.test_calc" name="test_add_passes" time="0.001"
          file="tests/test_calc.py" line="9"/>
<testcase classname="tests.test_calc" name="test_sub_fails" time="0.002"
          file="tests/test_calc.py" line="13">
<failure message="assert 8 == 2">def test_sub_fails(): ...</failure>
</testcase>
</testsuite>
</testsuites>"""
