#!/usr/bin/env python3
import sys
sys.path.append("third_party/appdirs")
sys.path.append("third_party/progressbar")
import unittest
import sky3ds.test_disk

suite = unittest.TestLoader()
suite = suite.loadTestsFromModule(sky3ds.test_disk)

unittest.TextTestRunner().run(suite)

