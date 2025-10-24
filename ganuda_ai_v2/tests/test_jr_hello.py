def hello_world():
    return 'Hello from Integration Jr'

def test_hello_world():
    result = hello_world()
    assert result == 'Hello from Integration Jr', f"Expected Hello from Integration Jr, got {result}"

if __name__ == "__main__":
    import unittest
    suite = unittest.TestLoader().loadTestsFromTestCase(test_hello_world)
    runner = unittest.TextTestRunner()
    runner.run(suite)